import hashlib
import secrets
import sqlite3

from app.models.db import get_connection


def generate_salt() -> bytes:
    return secrets.token_bytes(16)


def hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )
    return dk.hex()


class UserRepository:
    @staticmethod
    def create_user(username: str, password: str, nickname: str = "", email: str = "", status: int = 1) -> bool:
        salt = generate_salt()
        password_hash = hash_password(password, salt)
        try:
            with get_connection() as conn:
                conn.execute(
                    "insert into users(username, password_hash, salt, nickname, email, status) values(?, ?, ?, ?, ?, ?)",
                    (username, password_hash, salt.hex(), nickname, email, status)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_user_by_username(username: str):
        with get_connection() as conn:
            row = conn.execute(
                "select id, username, password_hash, salt, nickname, email, status, last_login_at, create_at from users where username = ?",
                (username,)
            ).fetchone()
        return row

    @staticmethod
    def get_user_by_id(user_id: int):
        with get_connection() as conn:
            row = conn.execute(
                "select id, username, nickname, email, status, last_login_at, create_at from users where id = ?",
                (user_id,)
            ).fetchone()
        return row

    @staticmethod
    def verify_user(username: str, password: str) -> bool:
        row = UserRepository.get_user_by_username(username)
        if not row:
            return False
        salt = bytes.fromhex(row["salt"])
        return hash_password(password, salt) == row["password_hash"]

    @staticmethod
    def get_user_list(page: int = 1, page_size: int = 20, keyword: str = "", status: str = "") -> dict:
        from app.models.role import UserRoleRepository
        offset = (page - 1) * page_size

        conditions = []
        params = []
        if keyword:
            conditions.append("username like ?")
            params.append(f"%{keyword}%")
        if status != "":
            conditions.append("status = ?")
            params.append(int(status))

        where = " WHERE " + " AND ".join(conditions) if conditions else ""

        with get_connection() as conn:
            total = conn.execute(f"SELECT count(*) FROM users{where}", params).fetchone()[0]
            rows = conn.execute(
                f"SELECT id, username, nickname, email, status, last_login_at, create_at FROM users{where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()

        data = []
        for row in rows:
            d = dict(row)
            roles = UserRoleRepository.get_user_role_names(d["id"])
            d["roles"] = ", ".join(roles) if roles else "未分配"
            data.append(d)

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
        }

    @staticmethod
    def update_user(user_id: int, username: str, nickname: str = "", email: str = "", password: str = "", status: int = 1) -> bool:
        with get_connection() as conn:
            if password:
                salt = generate_salt()
                password_hash = hash_password(password, salt)
                try:
                    conn.execute(
                        "update users set username=?, nickname=?, email=?, status=?, password_hash=?, salt=? where id=?",
                        (username, nickname, email, status, password_hash, salt.hex(), user_id)
                    )
                    return True
                except sqlite3.IntegrityError:
                    return False
            else:
                try:
                    conn.execute(
                        "update users set username=?, nickname=?, email=?, status=? where id=?",
                        (username, nickname, email, status, user_id)
                    )
                    return True
                except sqlite3.IntegrityError:
                    return False

    @staticmethod
    def update_password(user_id: int, new_password: str) -> bool:
        salt = generate_salt()
        new_hash = hash_password(new_password, salt)
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (new_hash, salt, user_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_login_time(user_id: int):
        with get_connection() as conn:
            conn.execute("UPDATE users SET last_login_at = datetime('now') WHERE id = ?", (user_id,))

    @staticmethod
    def delete_users(user_ids: list) -> int:
        if not user_ids:
            return 0
        placeholders = ",".join("?" for _ in user_ids)
        sql = f"delete from users where id in ({placeholders})"
        with get_connection() as conn:
            cursor = conn.execute(sql, user_ids)
            return cursor.rowcount

    @staticmethod
    def username_exists(username: str, exclude_id: int = 0) -> bool:
        with get_connection() as conn:
            if exclude_id > 0:
                row = conn.execute(
                    "select count(*) from users where username = ? and id != ?",
                    (username, exclude_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "select count(*) from users where username = ?",
                    (username,)
                ).fetchone()
        return row[0] > 0
