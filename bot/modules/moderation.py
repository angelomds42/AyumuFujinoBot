from datetime import datetime, timedelta, timezone
from telegram import Update, ChatMember, MessageEntity, constants
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


async def _check_common(update, context, s, action):
    if await _guard(
        update, s, not await is_user_admin(update), f"moderation.{action}_not_admin"
    ):
        return None, None, False

    if await _guard(
        update,
        s,
        not await bot_has_permission(update, "can_restrict_members"),
        f"moderation.{action}_bot_no_permission",
    ):
        return None, None, False

    user_id, display_name = await _resolve_target(update, context)

    if await _guard(update, s, not user_id, f"moderation.{action}_no_target"):
        return None, None, False
    if await _guard(
        update, s, user_id == update.effective_user.id, f"moderation.{action}_self"
    ):
        return None, None, False

    member = await _get_member(update.effective_chat, user_id)
    if member and await _guard(
        update,
        s,
        member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER),
        f"moderation.{action}_admin",
    ):
        return None, None, False

    return user_id, display_name, True


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    user_id, display_name, ok = await _check_common(update, context, s, "kick")
    if not ok:
        return

    reason_start = 1 if context.args and not update.message.reply_to_message else 0
    reason = " ".join(context.args[reason_start:]) if context.args else None

    try:
        await update.effective_chat.ban_member(user_id)
        await update.effective_chat.unban_member(user_id)

        text = s("moderation.kick_success", username=e(display_name))
        if reason:
            text += f"\n{s('moderation.kick_reason', reason=e(reason))}"

        await update.message.reply_text(
            text, parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    except TelegramError:
        await update.message.reply_text(
            s("moderation.kick_error"), parse_mode=constants.ParseMode.MARKDOWN_V2
        )


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    user_id, display_name, ok = await _check_common(update, context, s, "ban")
    if not ok:
        return

    arg_offset = 0 if update.message.reply_to_message else 1
    until_date = None
    duration_str = None

    if context.args and len(context.args) > arg_offset:
        delta = _parse_duration(context.args[arg_offset])
        if delta:
            until_date = datetime.now(tz=timezone.utc) + delta
            duration_str = context.args[arg_offset]
            arg_offset += 1

    reason = " ".join(context.args[arg_offset:]) if context.args else None

    try:
        await update.effective_chat.ban_member(user_id, until_date=until_date)

        text = s("moderation.ban_success", username=e(display_name))
        if duration_str:
            text += f"\n{s('moderation.ban_duration', duration=e(duration_str))}"
        if reason:
            text += f"\n{s('moderation.ban_reason', reason=e(reason))}"

        await update.message.reply_text(
            text, parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    except TelegramError:
        await update.message.reply_text(
            s("moderation.ban_error"), parse_mode=constants.ParseMode.MARKDOWN_V2
        )


def __init_module__(application):
    application.add_handler(CommandHandler("kick", kick))
    application.add_handler(CommandHandler("ban", ban))
    register_module_help("Moderation", "moderation.help")
