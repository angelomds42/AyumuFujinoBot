from telegram import Update, constants, helpers
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from bot.utils.admin import is_user_admin
from bot.utils.help import get_string_helper, register_module_help
from bot.utils.db import get_note, get_note_by_index, save_note, delete_note, list_notes

MD = constants.ParseMode.MARKDOWN_V2


async def _reply(update: Update, text: str, parse_mode=MD) -> None:
    await update.message.reply_text(text, parse_mode=parse_mode)


async def _send_note(update: Update, content: str, parse_mode: str | None) -> None:
    await update.message.reply_text(content, parse_mode=parse_mode or None)


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not await is_user_admin(update):
        return await _reply(update, s("moderation.user_not_admin"))

    if not context.args:
        return await _reply(update, s("notes.save_usage"))

    name = context.args[0].lower()
    parse_mode = None

    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        content = replied.text_markdown_v2 or replied.caption_markdown_v2
        if not content:
            return await _reply(update, s("notes.save_no_content"))
        parse_mode = MD
    elif len(context.args) < 2:
        return await _reply(update, s("notes.save_usage"))
    else:
        content = helpers.escape_markdown(" ".join(context.args[1:]), version=2)
        parse_mode = MD

    save_note(update.effective_chat.id, name, content, parse_mode)
    await _reply(update, s("notes.save_success", name=e(name)))


async def delnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not await is_user_admin(update):
        return await _reply(update, s("moderation.user_not_admin"))

    if not context.args:
        return await _reply(update, s("notes.delnote_usage"))

    name = context.args[0].lower()
    deleted = delete_note(update.effective_chat.id, name)

    key = "notes.delnote_success" if deleted else "notes.delnote_not_found"
    await _reply(update, s(key, name=e(name)))


async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    note_list = list_notes(update.effective_chat.id)

    if not note_list:
        return await _reply(update, s("notes.empty"))

    lines = "\n".join(f"`{i + 1}`\\.  `#{e(n)}`" for i, n in enumerate(note_list))
    await _reply(update, f"*{s('notes.list_header')}*\n{lines}")


async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not context.args or not context.args[0].isdigit():
        return await _reply(update, s("notes.get_usage"))

    result = get_note_by_index(update.effective_chat.id, int(context.args[0]))

    if not result:
        return await _reply(
            update, s("notes.not_found_index", index=e(context.args[0]))
        )

    _, content, parse_mode = result
    await _send_note(update, content, parse_mode)


async def get_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    name = text[1:].split()[0].lower() if text and text.startswith("#") else None

    if not name:
        return

    s, e = get_string_helper(update)
    result = get_note(update.effective_chat.id, name)

    if not result:
        return await _reply(update, s("notes.not_found", name=e(name)))

    content, parse_mode = result
    await _send_note(update, content, parse_mode)


def __init_module__(application):
    application.add_handler(CommandHandler("save", save))
    application.add_handler(CommandHandler("delnote", delnote))
    application.add_handler(CommandHandler("notes", notes))
    application.add_handler(CommandHandler("get", get))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(r"^#\w+"), get_notes)
    )
    register_module_help("Notes", "notes.help")
