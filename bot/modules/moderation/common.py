from datetime import datetime, timedelta, timezone
from telegram import Update, ChatMember, MessageEntity
from telegram.error import TelegramError
from bot.utils.admin import is_user_admin, bot_has_permission
from bot.utils.message import reply
from bot.modules.users import get_user_id


def _parse_duration(arg: str) -> timedelta | None:
    units = {
        "m": lambda n: timedelta(minutes=n),
        "h": lambda n: timedelta(hours=n),
        "d": lambda n: timedelta(days=n),
    }
    try:
        return units[arg[-1]](int(arg[:-1])) if arg[-1] in units else None
    except (ValueError, IndexError):
        return None


def _parse_args(context, arg_offset: int, has_duration: bool):
    """Returns (until_date, duration_str, new_arg_offset)."""
    if not has_duration or not context.args or len(context.args) <= arg_offset:
        return None, None, arg_offset

    delta = _parse_duration(context.args[arg_offset])
    if not delta:
        return None, None, arg_offset

    return (
        datetime.now(tz=timezone.utc) + delta,
        context.args[arg_offset],
        arg_offset + 1,
    )


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


async def get_member(chat, user_id):
    try:
        return await chat.get_member(user_id)
    except TelegramError:
        return None


async def guard(update, s, condition, key) -> bool:
    if condition:
        await reply(update, s(key))
        return True
    return False


async def check_common(update, context, s, action, check_admin_target=True):
    if await guard(
        update, s, not await is_user_admin(update), "common.user_not_admin"
    ):
        return None, None, False

    if await guard(
        update,
        s,
        not await bot_has_permission(update, "can_restrict_members"),
        "moderation.common.bot_no_permission",
    ):
        return None, None, False

    user_id, display_name = await _resolve_target(update, context)

    if await guard(update, s, not user_id, "moderation.common.no_target"):
        return None, None, False
    if await guard(
        update, s, user_id == update.effective_user.id, f"moderation.{action}.self"
    ):
        return None, None, False

    if check_admin_target:
        member = await get_member(update.effective_chat, user_id)
        if member and await guard(
            update,
            s,
            member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER),
            f"moderation.{action}.admin",
        ):
            return None, None, False

    return user_id, display_name, True
