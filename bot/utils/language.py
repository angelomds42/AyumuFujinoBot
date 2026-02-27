import os
import yaml
import logging


logger = logging.getLogger(__name__)


class LanguageManager:
    def __init__(self, languages_dir="bot/languages"):
        self.languages_dir = languages_dir
        self.strings = {}
        self.default_language = "en"
        self.load_languages()

    def load_languages(self):
        if not os.path.exists(self.languages_dir):
            os.makedirs(self.languages_dir)
            return

        for filename in os.listdir(self.languages_dir):
            if filename.endswith(".yml") or filename.endswith(".yaml"):
                lang_code = filename.split(".")[0]
                filepath = os.path.join(self.languages_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        self.strings[lang_code] = data if data else {}
                        logger.info(f"Loaded lang: {lang_code}")
                except Exception as e:
                    logger.error(f"Error loading {lang_code}: {e}")

    def get_string(self, key, lang_code="en", **kwargs):
        if lang_code:
            lang_code = lang_code[:2]

        lang_strings = self.strings.get(
            lang_code, self.strings.get(self.default_language, {})
        )

        keys = key.split(".")
        value = lang_strings
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                if lang_code != self.default_language:
                    return self.get_string(key, self.default_language, **kwargs)
                return f"Missing key: {key}"

        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Format error {key}: {e}")
                return value

        return value


def get_msg_string(update, key, **kwargs):
    from bot.utils.db import get_chat_language

    if update and update.effective_chat and update.effective_chat.type != "private":
        lang = get_chat_language(update.effective_chat.id)
    elif update and update.effective_user:
        lang = update.effective_user.language_code or "en"
    else:
        lang = "en"
    return lang_manager.get_string(key, lang, **kwargs)


lang_manager = LanguageManager()
get_string = lang_manager.get_string
