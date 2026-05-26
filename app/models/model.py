import sqlite3
import json
import httpx
from app.models.db import get_connection


def init_model_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS models(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                api_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                model_code TEXT NOT NULL,
                is_default INTEGER NOT NULL DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                max_tokens INTEGER NOT NULL DEFAULT 4096,
                temperature REAL NOT NULL DEFAULT 0.7,
                total_requests INTEGER NOT NULL DEFAULT 0,
                total_prompt_tokens INTEGER NOT NULL DEFAULT 0,
                total_completion_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                last_used_at TEXT,
                created_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_chats(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                messages TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'success',
                error_msg TEXT,
                created_at TEXT NOT NULL DEFAULT(datetime('now')),
                FOREIGN KEY(model_id) REFERENCES models(id)
            )
        """)

        existing = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
        if existing == 0:
            conn.execute(
                "INSERT INTO models(name, api_url, api_key, model_code, is_default, enabled) VALUES(?, ?, ?, ?, ?, ?)",
                ("AIGC-DeepSeek-V3", "https://aigc-api.aitoolcore.com/api/v1/chat/completions",
                 "sk-aigc-7300edb728b5ee7d5ccc9a15aeade201e80e22d6", "deepseek-v3", 1, 1)
            )


class ModelRepository:
    @staticmethod
    def get_all(page=1, page_size=6):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM models ORDER BY is_default DESC, id DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return {
            "data": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
        }

    @staticmethod
    def get_by_id(mid):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM models WHERE id = ?", (mid,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, api_url, api_key, model_code, max_tokens=4096, temperature=0.7):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO models(name, api_url, api_key, model_code, max_tokens, temperature) VALUES(?, ?, ?, ?, ?, ?)",
                    (name, api_url, api_key, model_code, max_tokens, temperature)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(mid, name, api_url, api_key, model_code, max_tokens=4096, temperature=0.7, enabled=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE models SET name=?, api_url=?, api_key=?, model_code=?, max_tokens=?, temperature=?, enabled=? WHERE id=?",
                    (name, api_url, api_key, model_code, max_tokens, temperature, enabled, mid)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(mid):
        with get_connection() as conn:
            conn.execute("DELETE FROM model_chats WHERE model_id = ?", (mid,))
            cursor = conn.execute("DELETE FROM models WHERE id = ?", (mid,))
            return cursor.rowcount > 0

    @staticmethod
    def set_default(mid):
        with get_connection() as conn:
            conn.execute("UPDATE models SET is_default = 0")
            conn.execute("UPDATE models SET is_default = 1 WHERE id = ?", (mid,))
        return True

    @staticmethod
    def get_default():
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM models WHERE is_default = 1 AND enabled = 1").fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_stats(mid, prompt_tokens, completion_tokens):
        total = prompt_tokens + completion_tokens
        with get_connection() as conn:
            conn.execute(
                "UPDATE models SET total_requests = total_requests + 1, total_prompt_tokens = total_prompt_tokens + ?, total_completion_tokens = total_completion_tokens + ?, total_tokens = total_tokens + ?, last_used_at = datetime('now') WHERE id = ?",
                (prompt_tokens, completion_tokens, total, mid)
            )

    @staticmethod
    def get_chat_history(mid, page=1, page_size=20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM model_chats WHERE model_id = ?", (mid,)).fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM model_chats WHERE model_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (mid, page_size, offset)
            ).fetchall()
        data = []
        for r in rows:
            d = dict(r)
            d["messages"] = json.loads(d["messages"]) if d["messages"] else []
            data.append(d)
        return {"data": data, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def add_chat(mid, messages, prompt_tokens, completion_tokens, status="success", error_msg=""):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO model_chats(model_id, messages, prompt_tokens, completion_tokens, total_tokens, status, error_msg) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (mid, json.dumps(messages, ensure_ascii=False), prompt_tokens, completion_tokens, prompt_tokens + completion_tokens, status, error_msg)
            )


async def call_model_api(api_url, api_key, model_code, messages, stream=False, max_tokens=4096, temperature=0.7):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_code,
        "messages": messages,
        "stream": stream,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        if stream:
            async with client.stream("POST", api_url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                                usage = data.get("usage", {})
                                if usage:
                                    yield {"usage": usage}
                        except json.JSONDecodeError:
                            pass
        else:
            response = await client.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            yield result
