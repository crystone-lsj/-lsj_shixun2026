import sqlite3
from app.models.db import get_connection


def init_user_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frontend_users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                nickname TEXT DEFAULT '',
                role TEXT NOT NULL DEFAULT 'user',
                status INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT DEFAULT '新对话',
                model_id INTEGER DEFAULT NULL,
                created_at TEXT NOT NULL DEFAULT(datetime('now')),
                updated_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                content TEXT NOT NULL DEFAULT '',
                model TEXT DEFAULT '',
                employee_alias TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT(datetime('now')),
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
            )
        """)


class FrontendUserRepository:
    @staticmethod
    def create_user(username, password, nickname="", role="user"):
        import hashlib, secrets
        salt = secrets.token_bytes(16)
        password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex()
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO frontend_users(username, password_hash, salt, nickname, role) VALUES(?,?,?,?,?)",
                    (username, password_hash, salt.hex(), nickname, role)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def verify_user(username, password):
        import hashlib
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, salt, nickname, role, status FROM frontend_users WHERE username = ?",
                (username,)
            ).fetchone()
        if not row:
            return None
        salt = bytes.fromhex(row["salt"])
        if hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex() != row["password_hash"]:
            return None
        return dict(row)


class ChatSessionRepository:
    @staticmethod
    def create(user_id, title="新对话", model_id=None):
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO chat_sessions(user_id, title, model_id) VALUES(?,?,?)",
                (user_id, title, model_id)
            )
            return cursor.lastrowid

    @staticmethod
    def get_sessions(user_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_session(session_id, user_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_title(session_id, title):
        with get_connection() as conn:
            conn.execute(
                "UPDATE chat_sessions SET title = ?, updated_at = datetime('now') WHERE id = ?",
                (title, session_id)
            )

    @staticmethod
    def delete(session_id, user_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            cursor = conn.execute(
                "DELETE FROM chat_sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id)
            )
            return cursor.rowcount > 0


class ChatMessageRepository:
    @staticmethod
    def add(session_id, role, content, model="", employee_alias=""):
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO chat_messages(session_id, role, content, model, employee_alias) VALUES(?,?,?,?,?)",
                (session_id, role, content, model, employee_alias)
            )
            return cursor.lastrowid

    @staticmethod
    def get_messages(session_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_last_messages(session_id, limit=10):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            ).fetchall()
        return [dict(r) for r in rows][::-1]
