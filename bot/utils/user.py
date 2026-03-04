from telegram import Update, MessageEntity
from telegram.error import TelegramError
from bot.utils.db import get_db

import re


async def resolve_target(update: Update, context):
    message = update.message

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        return (user.id, user.username or user.full_name) if user else (None, None)

    if not context.args:
        return None, None

    target = re.sub(r"[^\w@\-]", "", context.args[0])

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
                pass

        try:
            chat = await context.bot.get_chat(target)
            return chat.id, chat.username or chat.first_name
        except TelegramError:
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


def get_user_id(username: str) -> int | None:
    username = username.lstrip("@").lower()
    db = get_db()
    row = db.execute(
        "SELECT user_id FROM users WHERE LOWER(username) = ?", (username,)
    ).fetchone()
    return row[0] if row else None
