from telegram import Update, ChatMemberUpdated
from telegram.ext import ContextTypes, MessageHandler, ChatMemberHandler, filters
from bot.utils.user import get_user_id
from bot.utils.db import get_db


def _save_user_to_db(user):
    if not user or user.is_bot:
        return
    db = get_db()
    db.execute(
        """
        INSERT INTO users (user_id, username, full_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name
        """,
        (user.id, user.username, user.full_name),
    )
    db.commit()


async def _save_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.is_bot:
        return
    _save_user_to_db(user)


async def _save_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member_update: ChatMemberUpdated = update.chat_member
    if not member_update:
        return
    _save_user_to_db(member_update.new_chat_member.user)


def __init_module__(application):
    application.add_handler(MessageHandler(filters.ALL, _save_user), group=1)
    application.add_handler(
        ChatMemberHandler(_save_chat_member, ChatMemberHandler.CHAT_MEMBER), group=1
    )
