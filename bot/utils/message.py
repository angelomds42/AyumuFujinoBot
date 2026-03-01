from telegram import Update, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes

MD = constants.ParseMode.MARKDOWN_V2


async def reply(update: Update, text: str) -> None:
    await update.message.reply_text(text, parse_mode=MD)


async def reply_keyboard(
    update: Update, text: str, keyboard: InlineKeyboardMarkup
) -> None:
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=MD)


async def edit(
    update: Update, text: str, keyboard: InlineKeyboardMarkup | None = None
) -> None:
    await update.callback_query.edit_message_text(
        text, reply_markup=keyboard, parse_mode=MD
    )
