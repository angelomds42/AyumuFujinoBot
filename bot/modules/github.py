from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.help import get_string_helper, register_module_help
from bot.utils.message import reply
from github import Github
from github.GithubException import UnknownObjectException, GithubException
import asyncio


async def github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)

    if not context.args:
        return await reply(update, s("github.no_args"))

    try:
        user = await asyncio.to_thread(Github().get_user, context.args[0])
    except UnknownObjectException:
        return await reply(update, s("github.not_found"))
    except GithubException:
        return await reply(update, s("github.error"))

    await reply(
        update,
        f"*{s('github.user_info')}*\n"
        f"*{s('github.name')}*: {e(user.name or '')}\n"
        f"*{s('github.username')}*: {e(user.login or '')}\n"
        f"*Bio*: {e(user.bio or '')}\n"
        f"*{s('github.location')}*: {e(user.location or '')}\n"
        f"*{s('github.public_repos')}*: {e(user.public_repos or '')}\n"
        f"*{s('github.followers')}*: {e(user.followers or '')}\n"
        f"*URL*: {e(user.html_url or '')}",
    )


def __init_module__(application):
    application.add_handler(CommandHandler("github", github))
    register_module_help("GitHub", "github.help")
