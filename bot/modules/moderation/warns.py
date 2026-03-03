from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.error import TelegramError
from bot.utils.admin import is_user_admin
from bot.utils.help import get_string_helper
from bot.utils.message import reply
from bot.utils.db import (
    add_warn,
    get_warns,
    reset_warns,
    get_warn_limit,
    set_warn_limit,
)
from bot.modules.moderation.common import check_common, get_member


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    user_id, display_name, ok = await check_common(update, context, s, "warn")
    if not ok:
        return

    arg_offset = 0 if update.message.reply_to_message else 1
    reason = " ".join(context.args[arg_offset:]) if context.args else None

    count = add_warn(update.effective_chat.id, user_id, reason)
    limit = get_warn_limit(update.effective_chat.id)

    if count >= limit:
        try:
            await update.effective_chat.ban_member(user_id)
            reset_warns(update.effective_chat.id, user_id)
            await reply(
                update,
                s(
                    "moderation.warn.banned",
                    username=e(display_name),
                    count=e(count),
                    limit=e(limit),
                ),
            )
        except TelegramError:
            await reply(update, s("moderation.ban.error"))
        return

    text = s(
        "moderation.warn.warned",
        username=e(display_name),
        count=e(count),
        limit=e(limit),
    )
    if reason:
        text += f"\n{s('moderation.common.restriction_reason', reason=e(reason))}"
    await reply(update, text)


async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    user_id, display_name, ok = await check_common(update, context, s, "warn")
    if not ok:
        return

    warn_list = get_warns(update.effective_chat.id, user_id)
    limit = get_warn_limit(update.effective_chat.id)

    if not warn_list:
        return await reply(update, s("moderation.warn.none", username=e(display_name)))

    lines = "\n".join(
        f"`{i + 1}`\\. {e(reason) if reason else s('moderation.warn.no_reason')}"
        for i, (reason, _) in enumerate(warn_list)
    )
    await reply(
        update,
        s(
            "moderation.warn.list",
            username=e(display_name),
            count=e(len(warn_list)),
            limit=e(limit),
        )
        + f"\n{lines}",
    )


async def resetwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    user_id, display_name, ok = await check_common(update, context, s, "warn")
    if not ok:
        return

    reset_warns(update.effective_chat.id, user_id)
    await reply(update, s("moderation.warn.reset", username=e(display_name)))


async def warnlimit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not await is_user_admin(update):
        return await reply(update, s("common.user_not_admin"))

    if not context.args or not context.args[0].isdigit() or int(context.args[0]) < 1:
        return await reply(update, s("moderation.warn.limit_usage"))

    limit = int(context.args[0])
    set_warn_limit(update.effective_chat.id, limit)
    await reply(update, s("moderation.warn.limit_set", limit=e(limit)))


def __init_module__(application):
    application.add_handler(CommandHandler("warn", warn))
    application.add_handler(CommandHandler("warns", warns))
    application.add_handler(CommandHandler("resetwarn", resetwarn))
    application.add_handler(CommandHandler("warnlimit", warnlimit))
