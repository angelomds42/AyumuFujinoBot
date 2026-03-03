import re
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from bot.utils.admin import is_user_admin
from bot.utils.help import get_string_helper, register_module_help
from bot.utils.message import reply, MD
from bot.utils.db import (
    save_filter,
    delete_filter,
    list_filters,
    get_filters,
    delete_all_filters,
)


def _parse_keyword(args: list[str]) -> tuple[str, list[str]]:
    """Parses keyword from args, supporting quoted keywords.
    Returns (keyword, remaining_args).
    /filter "bom dia" resposta → ("bom dia", ["resposta"])
    /filter oi resposta        → ("oi", ["resposta"])
    """
    raw = " ".join(args)
    match = re.match(r'^"(.+?)"\s*(.*)', raw, re.DOTALL)
    if match:
        return match.group(1).lower().strip(), match.group(2).split()
    return args[0].lower(), args[1:]


async def filter_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not await is_user_admin(update):
        return await reply(update, s("common.user_not_admin"))

    if not context.args:
        return await reply(update, s("filters.save_usage"))

    keyword, remaining = _parse_keyword(context.args)

    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        response = replied.text or replied.caption
        if not response:
            return await reply(update, s("filters.no_content"))
    else:
        if not remaining:
            return await reply(update, s("filters.save_usage"))
        response = " ".join(remaining)

    save_filter(update.effective_chat.id, keyword, response)
    await reply(update, s("filters.save_success", keyword=e(keyword)))


async def filter_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not await is_user_admin(update):
        return await reply(update, s("common.user_not_admin"))

    if not context.args:
        return await reply(update, s("filters.remove_usage"))

    keyword, _ = _parse_keyword(context.args)
    deleted = delete_filter(update.effective_chat.id, keyword)

    key = "filters.remove_success" if deleted else "filters.not_found"
    await reply(update, s(key, keyword=e(keyword)))


async def filter_remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, _ = get_string_helper(update)

    if not await is_user_admin(update):
        return await reply(update, s("common.user_not_admin"))

    delete_all_filters(update.effective_chat.id)
    await reply(update, s("filters.remove_all_success"))


async def filter_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)
    keywords = list_filters(update.effective_chat.id)

    if not keywords:
        return await reply(update, s("filters.empty"))

    lines = "\n".join(f"\\- `{e(k)}`" for k in keywords)
    await reply(update, f"*{s('filters.list_header')}*\n{lines}")


async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    chat_filters = get_filters(update.effective_chat.id)

    for keyword, response in chat_filters:
        if keyword in text:
            await update.message.reply_text(response)
            return


def __init_module__(application):
    application.add_handler(CommandHandler("filter", filter_add))
    application.add_handler(CommandHandler("unfilter", filter_remove))
    application.add_handler(CommandHandler("stopall", filter_remove_all))
    application.add_handler(CommandHandler("filters", filter_list))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filters), group=2
    )
    register_module_help("Filters", "filters.help")
