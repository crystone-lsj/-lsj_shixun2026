# 数据库链接与建表
import os
import sqlite3


# 获得项目根路径的方法
def _project_root():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )

# 获得数据库文件路径
DB_PATH = os.path.join(_project_root(), "database", "app.db")

# 获得数据库连接
def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 
def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id integer PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                nickname TEXT DEFAULT '',
                email TEXT DEFAULT '',
                status INTEGER NOT NULL DEFAULT 1,
                last_login_at TEXT,
                create_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
            """
        )

        columns = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "nickname" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN nickname TEXT DEFAULT ''")
        if "email" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''")
        if "status" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN status INTEGER NOT NULL DEFAULT 1")
        if "last_login_at" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN last_login_at TEXT")

    from app.models.role import init_role_tables
    init_role_tables()

    from app.models.model import init_model_tables
    init_model_tables()

    from app.models.lookout import init_lookout_tables
    init_lookout_tables()

    from app.models.api_service import init_api_tables
    init_api_tables()

    from app.models.digital_employee import init_employee_tables
    init_employee_tables()

    from app.models.frontend_user import init_user_tables
    init_user_tables()

    # 迁移：将已有数据库中的"瞭望管理"改为"瞭源管理"
    with get_connection() as conn:
        conn.execute("UPDATE modules SET name = '瞭源管理' WHERE code = 'lookout_manage' AND name = '瞭望管理'")