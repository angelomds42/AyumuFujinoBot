from dataclasses import dataclass
from telegram import Update, helpers
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from bot.utils.admin import is_user_admin
from bot.utils.help import get_string_helper, register_module_help
from bot.utils.message import reply, MD
from bot.utils.db import get_note, get_note_by_index, save_note, delete_note, list_notes


@dataclass
class NoteMedia:
    content: str | None
    parse_mode: str | None
    file_id: str | None
    file_type: str | None


_MEDIA_TYPES: dict[str, str] = {
    "photo": "reply_photo",
    "video": "reply_video",
    "document": "reply_document",
    "audio": "reply_audio",
    "voice": "reply_voice",
    "sticker": "reply_sticker",
    "animation": "reply_animation",
}


def _extract_media(message) -> NoteMedia:
    for file_type, _ in _MEDIA_TYPES.items():
        media = getattr(message, file_type, None)
        if media:
            file_id = media[-1].file_id if isinstance(media, tuple) else media.file_id
            caption = message.caption_markdown_v2 or None
            return NoteMedia(caption, MD if caption else None, file_id, file_type)

    if message.text:
        return NoteMedia(message.text_markdown_v2, MD, None, None)

    return NoteMedia(None, None, None, None)


async def _send_note(update: Update, note: NoteMedia) -> None:
    msg = update.message
    send_method = _MEDIA_TYPES.get(note.file_type) if note.file_type else None

    if send_method:
        kwargs = (
            {"caption": note.content, "parse_mode": note.parse_mode}
            if note.content
            else {}
        )
        await getattr(msg, send_method)(note.file_id, **kwargs)
    elif note.content:
        await msg.reply_text(note.content, parse_mode=note.parse_mode)


def _note_from_row(row: tuple) -> NoteMedia:
    _, content, parse_mode, file_id, file_type = row
    return NoteMedia(content, parse_mode, file_id, file_type)


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not await is_user_admin(update):
        return await reply(update, s("moderation.common.user_not_admin"))

    if not context.args:
        return await reply(update, s("notes.save_usage"))

    name = context.args[0].lower()

    if update.message.reply_to_message:
        note = _extract_media(update.message.reply_to_message)
        if not note.content and not note.file_id:
            return await reply(update, s("notes.save_no_content"))
    elif len(context.args) < 2:
        return await reply(update, s("notes.save_usage"))
    else:
        note = NoteMedia(
            content=helpers.escape_markdown(" ".join(context.args[1:]), version=2),
            parse_mode=MD,
            file_id=None,
            file_type=None,
        )

    save_note(
        update.effective_chat.id,
        name,
        note.content,
        note.parse_mode,
        note.file_id,
        note.file_type,
    )
    await reply(update, s("notes.save_success", name=e(name)))


async def delnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not await is_user_admin(update):
        return await reply(update, s("moderation.common.user_not_admin"))

    if not context.args:
        return await reply(update, s("notes.delnote_usage"))

    name = context.args[0].lower()
    deleted = delete_note(update.effective_chat.id, name)

    key = "notes.delnote_success" if deleted else "notes.delnote_not_found"
    await reply(update, s(key, name=e(name)))


async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)
    note_list = list_notes(update.effective_chat.id)

    if not note_list:
        return await reply(update, s("notes.empty"))

    lines = "\n".join(f"`{i + 1}`\\.  `#{e(n)}`" for i, n in enumerate(note_list))
    await reply(update, f"*{s('notes.list_header')}*\n{lines}")


async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not context.args or not context.args[0].isdigit():
        return await reply(update, s("notes.get_usage"))

    result = get_note_by_index(update.effective_chat.id, int(context.args[0]))

    if not result:
        return await reply(update, s("notes.not_found_index", index=e(context.args[0])))

    await _send_note(update, _note_from_row(result))


async def handle_hashtag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    name = text[1:].split()[0].lower() if text and text.startswith("#") else None

    if not name:
        return

    s, e = get_string_helper(update)
    result = get_note(update.effective_chat.id, name)

    if not result:
        return await reply(update, s("notes.not_found", name=e(name)))

    content, parse_mode, file_id, file_type = result
    await _send_note(update, NoteMedia(content, parse_mode, file_id, file_type))


def __init_module__(application):
    application.add_handler(CommandHandler("save", save))
    application.add_handler(CommandHandler("delnote", delnote))
    application.add_handler(CommandHandler("notes", notes))
    application.add_handler(CommandHandler("get", get))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(r"^#\w+"), handle_hashtag)
    )
    register_module_help("Notes", "notes.help")
