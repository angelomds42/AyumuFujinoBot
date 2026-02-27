from telegram import Update, constants
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.admin import is_user_admin
from bot.utils.help import get_string_helper, register_module_help
from bot.utils.db import get_chat_language, set_chat_language
from bot.utils.language import lang_manager


async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, _ = get_string_helper(update)

    if not await is_user_admin(update):
        await update.message.reply_text(
            s("moderation.user_not_admin"), parse_mode=constants.ParseMode.MARKDOWN_V2
        )
        return

    available = list(lang_manager.strings.keys())

    if not context.args or context.args[0].lower() not in available:
        langs = e_list(available)
        await update.message.reply_text(
            s("settings.setlang_usage", langs=langs),
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )
        return

    lang = context.args[0].lower()
    set_chat_language(update.effective_chat.id, lang)

    await update.message.reply_text(
        s("settings.setlang_success", lang=lang),
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


def e_list(items):
    from telegram import helpers

    return ", ".join(f"`{helpers.escape_markdown(i, version=2)}`" for i in items)


def __init_module__(application):
    application.add_handler(CommandHandler("setlang", setlang))
    register_module_help("Settings", "settings.help")
