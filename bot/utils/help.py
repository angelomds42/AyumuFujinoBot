from telegram import InlineKeyboardButton, helpers
from typing import Dict, List
from bot.utils.language import get_msg_string

HELP_MODULES: Dict[str, str] = {}


def register_module_help(module_name: str, help_key: str):
    HELP_MODULES[module_name] = help_key


def get_help_keyboard(back_text: str = "« Back") -> List[List[InlineKeyboardButton]]:
    """Generates a keyboard with all registered modules in rows of 2."""
    buttons = [
        InlineKeyboardButton(name, callback_data=f"help_mod_{name}")
        for name in sorted(HELP_MODULES.keys())
    ]
    keyboard = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    keyboard.append([InlineKeyboardButton(back_text, callback_data="start_main")])
    return keyboard


def get_module_help(module_name: str):
    return HELP_MODULES.get(module_name)


def get_string_helper(update):
    """Returns (s, e) — localized string getter and MarkdownV2 escaper."""

    def s(key, **kwargs):
        return get_msg_string(update, key, **kwargs)

    def e(value):
        return helpers.escape_markdown(str(value), version=2)

    return s, e


def e_list(items: list) -> str:
    return ", ".join(f"`{helpers.escape_markdown(i, version=2)}`" for i in items)
