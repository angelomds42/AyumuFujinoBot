from datetime import datetime, timedelta, timezone
from telegram import ChatPermissions, Update, ChatMember, MessageEntity, constants
from telegram.ext import ContextTypes, CommandHandler
from telegram.error import TelegramError
from bot.utils.admin import is_user_admin, bot_has_permission
from bot.utils.help import get_string_helper, register_module_help
from bot.modules.users import get_user_id


def _parse_duration(arg: str) -> timedelta | None:
    units = {
        "m": lambda n: timedelta(minutes=n),
        "h": lambda n: timedelta(hours=n),
        "d": lambda n: timedelta(days=n),
    }
    try:
        number = int(arg[:-1])
        unit = arg[-1]
        return units[unit](number) if unit in units else None
    except (ValueError, IndexError):
        return None


async def _resolve_target(update: Update, context):
    message = update.message

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        return (user.id, user.username or user.full_name) if user else (None, None)

    if not context.args:
        return None, None

    target = context.args[0].strip()

    entities = list(message.parse_entities([MessageEntity.TEXT_MENTION]))
    if entities:
        ent = entities[0]
        return ent.user.id, ent.user.username or ent.user.full_name

    if target.startswith("@"):
        uid = get_user_id(target)
        if uid:
            try:
                chat = await context.bot.get_chat(uid)
                return chat.id, chat.username or chat.first_name
            except TelegramError:
                return uid, target.lstrip("@")
        return None, None

    if target.lstrip("-").isdigit():
        uid = int(target)
        try:
            member = await update.effective_chat.get_member(uid)
            return member.user.id, member.user.username or member.user.full_name
        except TelegramError:
            try:
                chat = await context.bot.get_chat(uid)
                return chat.id, chat.username or chat.first_name
            except TelegramError:
                return None, None

    return None, None


async def _get_member(chat, user_id):
    try:
        return await chat.get_member(user_id)
    except TelegramError:
        return None


async def _guard(update, s, condition, key) -> bool:
    if condition:
        await update.message.reply_text(
            s(key), parse_mode=constants.ParseMode.MARKDOWN_V2
        )
        return True
    return False


async def _check_common(update, context, s, action, check_admin_target=True):
    if await _guard(
        update, s, not await is_user_admin(update), "moderation.user_not_admin"
    ):
        return None, None, False

    if await _guard(
        update,
        s,
        not await bot_has_permission(update, "can_restrict_members"),
        "moderation.bot_no_permission",
    ):
        return None, None, False

    user_id, display_name = await _resolve_target(update, context)

    if await _guard(update, s, not user_id, "moderation.no_target"):
        return None, None, False
    if await _guard(
        update, s, user_id == update.effective_user.id, f"moderation.{action}_self"
    ):
        return None, None, False

    if check_admin_target:
        member = await _get_member(update.effective_chat, user_id)
        if member and await _guard(
            update,
            s,
            member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER),
            f"moderation.{action}_admin",
        ):
            return None, None, False

    return user_id, display_name, True


async def _ban_common(
    update,
    context,
    action,
    force_reply=False,
    delete_message=False,
    has_duration=True,
    kick=False,
):
    s, e = get_string_helper(update)

    if force_reply:
        if not update.message.reply_to_message:
            await update.message.reply_text(
                s(f"moderation.reply_required"),
                parse_mode=constants.ParseMode.MARKDOWN_V2,
            )
            return

    user_id, display_name, ok = await _check_common(update, context, s, action)
    if not ok:
        return

    arg_offset = 0 if update.message.reply_to_message else 1
    until_date = None
    duration_str = None

    if has_duration and context.args and len(context.args) > arg_offset:
        delta = _parse_duration(context.args[arg_offset])
        if delta:
            until_date = datetime.now(tz=timezone.utc) + delta
            duration_str = context.args[arg_offset]
            arg_offset += 1

    reason = " ".join(context.args[arg_offset:]) if context.args else None

    try:
        await update.effective_chat.ban_member(user_id, until_date=until_date)
        if kick:
            await update.effective_chat.unban_member(user_id)
        if delete_message and update.message.reply_to_message:
            await update.message.reply_to_message.delete()

        text = s(f"moderation.{action}_success", username=e(display_name))
        if duration_str:
            text += f"\n{s(f'moderation.{action}_duration', duration=e(duration_str))}"
        if reason:
            text += f"\n{s('moderation.restriction_reason', reason=e(reason))}"

        await update.message.reply_text(
            text, parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    except TelegramError:
        await update.message.reply_text(
            s(f"moderation.{action}_error"), parse_mode=constants.ParseMode.MARKDOWN_V2
        )


async def _mute_common(
    update,
    context,
    action,
    restrict=True,
):
    s, e = get_string_helper(update)

    user_id, display_name, ok = await _check_common(update, context, s, action)
    if not ok:
        return

    member = await _get_member(update.effective_chat, user_id)

    if not restrict:
        if await _guard(
            update,
            s,
            not member or member.can_send_messages is not False,
            "moderation.unmute_not_muted",
        ):
            return

    arg_offset = 0 if update.message.reply_to_message else 1
    until_date = None
    duration_str = None

    if restrict and context.args and len(context.args) > arg_offset:
        delta = _parse_duration(context.args[arg_offset])
        if delta:
            until_date = datetime.now(tz=timezone.utc) + delta
            duration_str = context.args[arg_offset]
            arg_offset += 1

    reason = " ".join(context.args[arg_offset:]) if context.args else None

    try:
        allow = not restrict
        permissions = ChatPermissions(
            can_send_messages=allow,
            can_send_polls=allow,
            can_send_other_messages=allow,
            can_add_web_page_previews=allow,
        )

        await update.effective_chat.restrict_member(
            user_id, permissions, until_date=until_date
        )

        text = s(f"moderation.{action}_success", username=e(display_name))
        if duration_str:
            text += f"\n{s(f'moderation.{action}_duration', duration=e(duration_str))}"
        if reason:
            text += f"\n{s('moderation.restriction_reason', reason=e(reason))}"

        await update.message.reply_text(
            text, parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    except TelegramError:
        await update.message.reply_text(
            s(f"moderation.{action}_error"), parse_mode=constants.ParseMode.MARKDOWN_V2
        )


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ban_common(update, context, "kick", kick=True)


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ban_common(update, context, "ban")


async def dban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ban_common(update, context, "ban", force_reply=True, delete_message=True)


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    user_id, display_name, ok = await _check_common(
        update, context, s, "unban", check_admin_target=False
    )
    if not ok:
        return

    member = await _get_member(update.effective_chat, user_id)
    if await _guard(
        update,
        s,
        not member or member.status != ChatMember.BANNED,
        "moderation.unban_not_banned",
    ):
        return

    reason_start = 1 if context.args and not update.message.reply_to_message else 0
    reason = " ".join(context.args[reason_start:]) if context.args else None

    try:
        await update.effective_chat.unban_member(user_id)

        text = s("moderation.unban_success", username=e(display_name))
        if reason:
            text += f"\n{s('moderation.restriction_reason', reason=e(reason))}"

        await update.message.reply_text(
            text, parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    except TelegramError:
        await update.message.reply_text(
            s("moderation.unban_error"), parse_mode=constants.ParseMode.MARKDOWN_V2
        )


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _mute_common(update, context, "mute")


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _mute_common(update, context, "unmute", restrict=False)


def __init_module__(application):
    application.add_handler(CommandHandler("kick", kick))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("dban", dban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("unmute", unmute))
    register_module_help("Moderation", "moderation.help")
