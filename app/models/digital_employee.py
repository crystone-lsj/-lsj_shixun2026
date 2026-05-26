import sqlite3
import json
from app.models.db import get_connection


def init_employee_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS digital_employees(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                alias TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT 'normal',
                description TEXT DEFAULT '',
                config TEXT DEFAULT '{}',
                prompt TEXT DEFAULT '',
                api_id INTEGER DEFAULT NULL,
                icon TEXT DEFAULT '',
                color TEXT DEFAULT '#6366f1',
                status INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)

        rows = conn.execute("SELECT COUNT(*) FROM digital_employees").fetchone()[0]
        if rows == 0:
            api_ids = {}
            api_rows = conn.execute("SELECT id, category FROM api_services").fetchall()
            for r in api_rows:
                api_ids[r["category"]] = r["id"]

            conn.execute(
                "INSERT INTO digital_employees(name, alias, category, description, config, prompt, icon, color, status) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("川小农", "川小码", "ai", "智能农业助手，基于大模型的智能对话服务", '{"model_id": null, "temperature": 0.7, "max_tokens": 2000}', "你是一个名为'川小农'的AI农业助手，擅长农业相关问题的解答。请用简洁明了的方式回答用户的问题。", "fas fa-robot", "#6366f1", 1)
            )

            weather_api_id = api_ids.get("天气")
            conn.execute(
                "INSERT INTO digital_employees(name, alias, category, description, config, prompt, api_id, icon, color, status) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("天气查询", "天气", "normal", "天气查询服务，通过API获取实时天气数据", '{"api_param": "city"}', "", weather_api_id, "fas fa-cloud-sun", "#1e9fff", 1)
            )

            music_api_id = api_ids.get("音乐")
            conn.execute(
                "INSERT INTO digital_employees(name, alias, category, description, config, prompt, api_id, icon, color, status) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("随机音乐", "音乐", "normal", "随机音乐推荐服务，获取随机歌曲", '{}', "", music_api_id, "fas fa-music", "#ff6b81", 1)
            )


class DigitalEmployeeRepository:
    @staticmethod
    def get_list(page=1, page_size=20, keyword="", category="", status=""):
        offset = (page - 1) * page_size
        conditions = []
        params = []
        if keyword:
            conditions.append("(name like ? or alias like ? or description like ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        if category:
            conditions.append("category = ?")
            params.append(category)
        if status != "":
            conditions.append("status = ?")
            params.append(int(status))
        where = " WHERE " + " AND ".join(conditions) if conditions else ""

        with get_connection() as conn:
            total = conn.execute(f"SELECT count(*) FROM digital_employees{where}", params).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM digital_employees{where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
        return {"data": [dict(r) for r in rows], "total": total}

    @staticmethod
    def get_by_id(emp_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM digital_employees WHERE id = ?", (emp_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_alias(alias):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM digital_employees WHERE alias = ? AND status = 1", (alias,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all_active():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM digital_employees WHERE status = 1 ORDER BY id"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def create(name, alias, category="normal", description="", config="{}", prompt="",
               api_id=None, icon="", color="#6366f1", status=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO digital_employees(name, alias, category, description, config, prompt, api_id, icon, color, status) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, alias, category, description, config, prompt, api_id, icon, color, status)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(emp_id, name, alias, category="normal", description="", config="{}", prompt="",
               api_id=None, icon="", color="#6366f1", status=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE digital_employees SET name=?, alias=?, category=?, description=?, config=?, prompt=?, api_id=?, icon=?, color=?, status=? WHERE id=?",
                    (name, alias, category, description, config, prompt, api_id, icon, color, status, emp_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(emp_id):
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM digital_employees WHERE id = ?", (emp_id,))
            return cursor.rowcount > 0
