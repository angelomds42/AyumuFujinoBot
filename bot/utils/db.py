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
                content    TEXT,
                parse_mode TEXT,
                file_id    TEXT,
                file_type  TEXT,
                PRIMARY KEY (chat_id, name)
            )
        """
        )
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS warns (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id  INTEGER NOT NULL,
                user_id  INTEGER NOT NULL,
                reason   TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS warn_settings (
                chat_id    INTEGER PRIMARY KEY,
                warn_limit INTEGER NOT NULL DEFAULT 3
            )
        """
        )
        _conn.commit()

        for migration in [
            "ALTER TABLE notes ADD COLUMN parse_mode TEXT",
            "ALTER TABLE notes ADD COLUMN file_id TEXT",
            "ALTER TABLE notes ADD COLUMN file_type TEXT",
        ]:
            try:
                _conn.execute(migration)
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


def get_note(chat_id: int, name: str) -> tuple | None:
    row = (
        get_db()
        .execute(
            "SELECT content, parse_mode, file_id, file_type FROM notes WHERE chat_id = ? AND LOWER(name) = ?",
            (chat_id, name.lower()),
        )
        .fetchone()
    )
    return tuple(row) if row else None


def get_note_by_index(chat_id: int, index: int) -> tuple | None:
    rows = (
        get_db()
        .execute(
            "SELECT name, content, parse_mode, file_id, file_type FROM notes WHERE chat_id = ? ORDER BY name",
            (chat_id,),
        )
        .fetchall()
    )
    return rows[index - 1] if 0 < index <= len(rows) else None


def save_note(
    chat_id: int,
    name: str,
    content: str | None = None,
    parse_mode: str | None = None,
    file_id: str | None = None,
    file_type: str | None = None,
) -> None:
    db = get_db()
    db.execute(
        """
        INSERT INTO notes (chat_id, name, content, parse_mode, file_id, file_type)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(chat_id, name) DO UPDATE SET
            content    = excluded.content,
            parse_mode = excluded.parse_mode,
            file_id    = excluded.file_id,
            file_type  = excluded.file_type
        """,
        (chat_id, name.lower(), content, parse_mode, file_id, file_type),
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


def add_warn(chat_id: int, user_id: int, reason: str | None = None) -> int:
    db = get_db()
    db.execute(
        "INSERT INTO warns (chat_id, user_id, reason) VALUES (?, ?, ?)",
        (chat_id, user_id, reason),
    )
    db.commit()
    row = db.execute(
        "SELECT COUNT(*) FROM warns WHERE chat_id = ? AND user_id = ?",
        (chat_id, user_id),
    ).fetchone()
    return row[0]


def get_warns(chat_id: int, user_id: int) -> list[tuple[str | None, str]]:
    rows = (
        get_db()
        .execute(
            "SELECT reason, added_at FROM warns WHERE chat_id = ? AND user_id = ? ORDER BY added_at",
            (chat_id, user_id),
        )
        .fetchall()
    )
    return rows


def reset_warns(chat_id: int, user_id: int) -> bool:
    db = get_db()
    cursor = db.execute(
        "DELETE FROM warns WHERE chat_id = ? AND user_id = ?",
        (chat_id, user_id),
    )
    db.commit()
    return cursor.rowcount > 0


def get_warn_limit(chat_id: int) -> int:
    row = (
        get_db()
        .execute("SELECT warn_limit FROM warn_settings WHERE chat_id = ?", (chat_id,))
        .fetchone()
    )
    return row[0] if row else 3


def set_warn_limit(chat_id: int, limit: int) -> None:
    db = get_db()
    db.execute(
        """
        INSERT INTO warn_settings (chat_id, warn_limit) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET warn_limit = excluded.warn_limit
        """,
        (chat_id, limit),
    )
    db.commit()
