from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from bot.utils.help import (
    get_help_keyboard,
    get_module_help,
    get_string_helper,
    register_module_help,
)


async def send_menu(update: Update, text_key: str, keyboard: list):
    s, _ = get_string_helper(update)
    text = s(text_key)
    markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=markup, parse_mode=constants.ParseMode.MARKDOWN_V2
        )
    else:
        await update.message.reply_text(
            text, reply_markup=markup, parse_mode=constants.ParseMode.MARKDOWN_V2
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, _ = get_string_helper(update)
    keyboard = [[InlineKeyboardButton(s("common.btn_help"), callback_data="help_main")]]
    await send_menu(update, "common.start", keyboard)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    s, _ = get_string_helper(update)

    if data == "start_main":
        await start(update, context)
    elif data == "help_main":
        await send_menu(update, "common.help", get_help_keyboard())
    elif data.startswith("help_mod_"):
        mod_name = data.replace("help_mod_", "")
        help_key = get_module_help(mod_name)
        if help_key:
            keyboard = [
                [InlineKeyboardButton(s("common.back"), callback_data="help_main")]
            ]
            await send_menu(update, help_key, keyboard)


def __init_module__(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        CommandHandler(
            "help", lambda u, c: send_menu(u, "common.help", get_help_keyboard())
        )
    )
    application.add_handler(
        CallbackQueryHandler(menu_handler, pattern="^(help_|start_)")
    )
    register_module_help("Basics", "basics.help")
