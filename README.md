# Ayumu Fujino

Another Python modular Telegram group management bot.

## Setup

**Requirements:** Python 3.12+

```bash
git clone https://github.com/angelomds42/AyumuFujinoBot
cd AyumuFujinoBot
pip install -r requirements.txt
```

Create a `.env` file:

```env
BOT_TOKEN=your_token_here
```

Run:

```bash
python -m bot
```

## Adding a Module

Create a file in `bot/modules/`. The bot auto-loads any module that exposes `__init_module__`:

```python
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.help import get_string_helper, register_module_help
from bot.utils.message import reply

async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, e = get_string_helper(update)
    await reply(update, s("my_module.my_string"))

def __init_module__(application):
    application.add_handler(CommandHandler("mycommand", my_command))
    register_module_help("MyModule", "my_module.help")
```

See `bot/modules/example/example.py` for a full reference.
