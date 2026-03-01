from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.admin import is_user_admin
from bot.utils.help import get_string_helper, register_module_help, e_list
from bot.utils.message import reply
from bot.utils.db import set_chat_language
from bot.utils.language import lang_manager


async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, _ = get_string_helper(update)

    if not await is_user_admin(update):
        return await reply(update, s("moderation.user_not_admin"))

    available = list(lang_manager.strings.keys())

    if not context.args or context.args[0].lower() not in available:
        return await reply(update, s("settings.setlang_usage", langs=e_list(available)))

    lang = context.args[0].lower()
    set_chat_language(update.effective_chat.id, lang)
    await reply(update, s("settings.setlang_success", lang=lang))


def __init_module__(application):
    application.add_handler(CommandHandler("setlang", setlang))
    register_module_help("Settings", "settings.help")
