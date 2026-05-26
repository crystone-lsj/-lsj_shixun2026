import json
import sqlite3
from app.models.db import get_connection


def init_lookout_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lookout_sources(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url_template TEXT NOT NULL,
                headers TEXT NOT NULL DEFAULT '{}',
                param_fields TEXT NOT NULL DEFAULT '[]',
                selector_title TEXT,
                selector_content TEXT,
                selector_time TEXT,
                selector_source TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lookout_data(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                content TEXT,
                url TEXT,
                source_name TEXT,
                publish_time TEXT,
                collected_at TEXT NOT NULL DEFAULT(datetime('now')),
                FOREIGN KEY(source_id) REFERENCES lookout_sources(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_lookout_data_source ON lookout_data(source_id)
        """)

        cnt = conn.execute("SELECT COUNT(*) FROM lookout_sources").fetchone()[0]
        if cnt == 0:
            baidu_headers = json.dumps({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "Referer": "https://news.baidu.com/"
            }, ensure_ascii=False)
            baidu_params = json.dumps([
                {"field": "keyword", "label": "关键字", "type": "text", "required": True, "default": ""},
                {"field": "pn", "label": "分页步进", "type": "number", "required": False, "default": "0"}
            ], ensure_ascii=False)
            conn.execute(
                "INSERT INTO lookout_sources(name, url_template, headers, param_fields, selector_title, selector_content, selector_time, selector_source) VALUES(?,?,?,?,?,?,?,?)",
                ("百度新闻", "https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&rsv_dl=ns_pc&word={keyword}&pn={pn}",
                 baidu_headers, baidu_params,
                 "h3.news-title_1YvLe a", "div.c-span-last, span.c-color-gray2.c-span-last",
                 "span.c-color-gray2.c-span-last, span.news-time_1MqF6", "span.c-span-last.c-color-source")
            )


class LookoutSourceRepository:
    @staticmethod
    def get_all():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM lookout_sources ORDER BY id").fetchall()
            data = []
            for r in rows:
                d = dict(r)
                d["headers"] = json.loads(d["headers"]) if d["headers"] else {}
                d["param_fields"] = json.loads(d["param_fields"]) if d["param_fields"] else []
                data.append(d)
            return data

    @staticmethod
    def get_by_id(sid):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM lookout_sources WHERE id = ?", (sid,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["headers"] = json.loads(d["headers"]) if d["headers"] else {}
            d["param_fields"] = json.loads(d["param_fields"]) if d["param_fields"] else []
            return d

    @staticmethod
    def create(name, url_template, headers="{}", param_fields="[]", selector_title="", selector_content="", selector_time="", selector_source="", enabled=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO lookout_sources(name, url_template, headers, param_fields, selector_title, selector_content, selector_time, selector_source, enabled) VALUES(?,?,?,?,?,?,?,?,?)",
                    (name, url_template, headers, param_fields, selector_title, selector_content, selector_time, selector_source, enabled)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(sid, name, url_template, headers="{}", param_fields="[]", selector_title="", selector_content="", selector_time="", selector_source="", enabled=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE lookout_sources SET name=?, url_template=?, headers=?, param_fields=?, selector_title=?, selector_content=?, selector_time=?, selector_source=?, enabled=? WHERE id=?",
                    (name, url_template, headers, param_fields, selector_title, selector_content, selector_time, selector_source, enabled, sid)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(sid):
        with get_connection() as conn:
            conn.execute("DELETE FROM lookout_data WHERE source_id = ?", (sid,))
            cursor = conn.execute("DELETE FROM lookout_sources WHERE id = ?", (sid,))
            return cursor.rowcount > 0


class LookoutDataRepository:
    @staticmethod
    def get_list(page=1, page_size=20, keyword=""):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            if keyword:
                pattern = f"%{keyword}%"
                total = conn.execute(
                    "SELECT COUNT(*) FROM lookout_data d JOIN lookout_sources s ON d.source_id = s.id WHERE d.title LIKE ? OR s.name LIKE ?",
                    (pattern, pattern)
                ).fetchone()[0]
                rows = conn.execute(
                    """SELECT d.id, d.title, d.summary, d.url, d.source_name, d.publish_time, d.collected_at, s.name as source_name 
                       FROM lookout_data d JOIN lookout_sources s ON d.source_id = s.id 
                       WHERE d.title LIKE ? OR d.source_name LIKE ? 
                       ORDER BY d.id DESC LIMIT ? OFFSET ?""",
                    (pattern, pattern, page_size, offset)
                ).fetchall()
            else:
                total = conn.execute("SELECT COUNT(*) FROM lookout_data").fetchone()[0]
                rows = conn.execute(
                    """SELECT d.id, d.title, d.summary, d.url, d.source_name, d.publish_time, d.collected_at, s.name as source_name 
                       FROM lookout_data d JOIN lookout_sources s ON d.source_id = s.id 
                       ORDER BY d.id DESC LIMIT ? OFFSET ?""",
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
    def delete(ids):
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with get_connection() as conn:
            cursor = conn.execute(f"DELETE FROM lookout_data WHERE id IN ({placeholders})", ids)
            return cursor.rowcount

    @staticmethod
    def save(source_id, title, summary="", content="", url="", source_name="", publish_time=""):
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO lookout_data(source_id, title, summary, content, url, source_name, publish_time) VALUES(?,?,?,?,?,?,?)",
                (source_id, title, summary, content, url, source_name, publish_time)
            )
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    @staticmethod
    def batch_save(items):
        count = 0
        with get_connection() as conn:
            for item in items:
                conn.execute(
                    "INSERT INTO lookout_data(source_id, title, summary, content, url, source_name, publish_time) VALUES(?,?,?,?,?,?,?)",
                    (item.get("source_id"), item.get("title", ""), item.get("summary", ""),
                     item.get("content", ""), item.get("url", ""), item.get("source_name", ""),
                     item.get("publish_time", ""))
                )
                count += 1
        return count
