import sqlite3
import json
from app.models.db import get_connection


def init_api_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_services(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'GET',
                response_format TEXT DEFAULT 'JSON',
                qps TEXT DEFAULT '',
                description TEXT DEFAULT '',
                category TEXT DEFAULT '',
                token_required INTEGER NOT NULL DEFAULT 0,
                status INTEGER NOT NULL DEFAULT 1,
                example_response TEXT DEFAULT '',
                headers TEXT DEFAULT '{}',
                params TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT(datetime('now')),
                updated_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)

        rows = conn.execute("SELECT COUNT(*) FROM api_services").fetchone()[0]
        if rows == 0:
            conn.execute(
                "INSERT INTO api_services(name, url, method, response_format, qps, description, category, example_response) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                ("随机音乐API", "https://api.52vmy.cn/api/music/wy/rand", "GET", "JSON", "每2秒最多4次 携带Token可无视限制", "", "音乐", '{"code":200,"msg":"成功","data":{"song":"悬溺","singer":"葛东琪","cover":"http://p1.music.126.net/CDhYcShQKH2VAMENuCxWWQ==/109951164166513349.jpg","Music":"http://music.163.com/song/media/outer/url?id=1397345903","id":1397345903}}')
            )
            conn.execute(
                "INSERT INTO api_services(name, url, method, response_format, qps, description, category, example_response) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                ("三日天气API", "https://api.52vmy.cn/api/query/tian", "GET", "JSON", "每2秒最多4次 携带Token可无视限制", "点击前往三日天气API", "天气", '{"code":200,"msg":"成功","data":{}}')
            )


class ApiServiceRepository:
    @staticmethod
    def get_list(page=1, page_size=20, keyword="", category="", status=""):
        offset = (page - 1) * page_size
        conditions = []
        params = []
        if keyword:
            conditions.append("(name like ? or url like ? or description like ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        if category:
            conditions.append("category = ?")
            params.append(category)
        if status != "":
            conditions.append("status = ?")
            params.append(int(status))
        where = " WHERE " + " AND ".join(conditions) if conditions else ""

        with get_connection() as conn:
            total = conn.execute(f"SELECT count(*) FROM api_services{where}", params).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM api_services{where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
        return {"data": [dict(r) for r in rows], "total": total}

    @staticmethod
    def get_by_id(api_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM api_services WHERE id = ?", (api_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, url, method="GET", response_format="JSON", qps="", description="",
               category="", token_required=0, status=1, example_response="", headers="{}", params="{}"):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO api_services(name, url, method, response_format, qps, description, category, token_required, status, example_response, headers, params) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, url, method, response_format, qps, description, category, token_required, status, example_response, headers, params)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(api_id, name, url, method="GET", response_format="JSON", qps="", description="",
               category="", token_required=0, status=1, example_response="", headers="{}", params="{}"):
        with get_connection() as conn:
            conn.execute(
                "UPDATE api_services SET name=?, url=?, method=?, response_format=?, qps=?, description=?, category=?, token_required=?, status=?, example_response=?, headers=?, params=?, updated_at=datetime('now') WHERE id=?",
                (name, url, method, response_format, qps, description, category, token_required, status, example_response, headers, params, api_id)
            )
        return True

    @staticmethod
    def delete(api_id):
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM api_services WHERE id = ?", (api_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_categories():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM api_services WHERE category != '' ORDER BY category"
            ).fetchall()
        return [r["category"] for r in rows]
