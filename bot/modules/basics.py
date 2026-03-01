from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from bot.utils.help import (
    get_help_keyboard,
    get_module_help,
    get_string_helper,
    register_module_help,
)
from bot.utils.message import reply_keyboard, edit


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, _ = get_string_helper(update)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(s("common.btn_help"), callback_data="help_main")]]
    )

    if update.effective_chat.type != "private":
        await reply_keyboard(update, s("common.start_group"), keyboard)
        return

    await reply_keyboard(update, s("common.start"), keyboard)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    s, _ = get_string_helper(update)

    if query.data == "start_main":
        await start(update, context)
    elif query.data == "help_main":
        keyboard = InlineKeyboardMarkup(get_help_keyboard(s("common.back")))
        await edit(update, s("common.help"), keyboard)
    elif query.data.startswith("help_mod_"):
        mod_name = query.data.replace("help_mod_", "")
        help_key = get_module_help(mod_name)
        if help_key:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(s("common.back"), callback_data="help_main")]]
            )
            await edit(update, s(help_key), keyboard)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, _ = get_string_helper(update)
    keyboard = InlineKeyboardMarkup(get_help_keyboard(s("common.back")))
    await reply_keyboard(update, s("common.help"), keyboard)


def __init_module__(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(
        CallbackQueryHandler(menu_handler, pattern="^(help_|start_)")
    )
    register_module_help("Basics", "basics.help")
