import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "bot", "data", "bot.db")

_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _conn = sqlite3.connect(DB_PATH)
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id  INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT
            )
            """
        )
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id  INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'en'
            )
            """
        )
    return _conn


def get_chat_language(chat_id: int) -> str:
    db = get_db()
    row = db.execute(
        "SELECT language FROM chats WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    return row[0] if row else "en"


def set_chat_language(chat_id: int, language: str) -> None:
    db = get_db()
    db.execute(
        """
        INSERT INTO chats (chat_id, language)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET language = excluded.language
        """,
        (chat_id, language),
    )
    db.commit()
