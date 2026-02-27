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
                user_id   INTEGER PRIMARY KEY,
                username  TEXT,
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
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                chat_id    INTEGER NOT NULL,
                name       TEXT NOT NULL,
                content    TEXT NOT NULL,
                parse_mode TEXT,
                PRIMARY KEY (chat_id, name)
            )
        """
        )
        _conn.commit()

        try:
            _conn.execute("ALTER TABLE notes ADD COLUMN parse_mode TEXT")
            _conn.commit()
        except sqlite3.OperationalError:
            pass

    return _conn


def get_chat_language(chat_id: int) -> str:
    row = (
        get_db()
        .execute("SELECT language FROM chats WHERE chat_id = ?", (chat_id,))
        .fetchone()
    )
    return row[0] if row else "en"


def set_chat_language(chat_id: int, language: str) -> None:
    db = get_db()
    db.execute(
        """
        INSERT INTO chats (chat_id, language) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET language = excluded.language
        """,
        (chat_id, language),
    )
    db.commit()


def get_note(chat_id: int, name: str) -> tuple[str, str | None] | None:
    row = (
        get_db()
        .execute(
            "SELECT content, parse_mode FROM notes WHERE chat_id = ? AND LOWER(name) = ?",
            (chat_id, name.lower()),
        )
        .fetchone()
    )
    return (row[0], row[1]) if row else None


def get_note_by_index(chat_id: int, index: int) -> tuple[str, str, str | None] | None:
    rows = (
        get_db()
        .execute(
            "SELECT name, content, parse_mode FROM notes WHERE chat_id = ? ORDER BY name",
            (chat_id,),
        )
        .fetchall()
    )
    return rows[index - 1] if 0 < index <= len(rows) else None


def save_note(
    chat_id: int, name: str, content: str, parse_mode: str | None = None
) -> None:
    db = get_db()
    db.execute(
        """
        INSERT INTO notes (chat_id, name, content, parse_mode) VALUES (?, ?, ?, ?)
        ON CONFLICT(chat_id, name) DO UPDATE SET
            content    = excluded.content,
            parse_mode = excluded.parse_mode
        """,
        (chat_id, name.lower(), content, parse_mode),
    )
    db.commit()


def delete_note(chat_id: int, name: str) -> bool:
    db = get_db()
    cursor = db.execute(
        "DELETE FROM notes WHERE chat_id = ? AND LOWER(name) = ?",
        (chat_id, name.lower()),
    )
    db.commit()
    return cursor.rowcount > 0


def list_notes(chat_id: int) -> list[str]:
    rows = (
        get_db()
        .execute("SELECT name FROM notes WHERE chat_id = ? ORDER BY name", (chat_id,))
        .fetchall()
    )
    return [row[0] for row in rows]
