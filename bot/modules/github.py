from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.help import register_module_help
from bot.utils.language import get_msg_string
from github import Github
from github.GithubException import UnknownObjectException, GithubException
import asyncio


async def github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            get_msg_string(update, "github.no_args"), parse_mode="Markdown"
        )
        return

    try:
        user = await asyncio.to_thread(Github().get_user, context.args[0])
    except UnknownObjectException:
        await update.message.reply_text(
            get_msg_string(update, "github.not_found"), parse_mode="Markdown"
        )
        return
    except GithubException:
        await update.message.reply_text(
            get_msg_string(update, "github.error"), parse_mode="Markdown"
        )
        return

    def s(key):
        return get_msg_string(update, key)

    await update.message.reply_text(
        f"*{s('github.user_info')}*:\n"
        f"*{s('github.name')}*: {user.name or ''}\n"
        f"*{s('github.username')}*: {user.login or ''}\n"
        f"*Bio*: {user.bio or ''}\n"
        f"*{s('github.location')}*: {user.location or ''}\n"
        f"*{s('github.public_repos')}*: {user.public_repos or ''}\n"
        f"*{s('github.followers')}*: {user.followers or ''}\n"
        f"*URL:* {user.html_url or ''}",
        parse_mode="Markdown",
    )


def __init_module__(application):
    application.add_handler(CommandHandler("github", github))
    register_module_help("GitHub", "github.help")
