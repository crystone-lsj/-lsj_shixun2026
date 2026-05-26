import sqlite3
from app.models.db import get_connection


def init_role_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS roles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                code TEXT NOT NULL UNIQUE DEFAULT '',
                status INTEGER NOT NULL DEFAULT 1,
                description TEXT DEFAULT '',
                is_system INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT(datetime('now'))
            )
        """)

        columns = [r["name"] for r in conn.execute("PRAGMA table_info(roles)").fetchall()]
        if "code" not in columns:
            conn.execute("ALTER TABLE roles ADD COLUMN code TEXT NOT NULL DEFAULT ''")
        if "status" not in columns:
            conn.execute("ALTER TABLE roles ADD COLUMN status INTEGER NOT NULL DEFAULT 1")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS permissions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                permission TEXT NOT NULL,
                label TEXT NOT NULL,
                parent_id INTEGER DEFAULT 0,
                UNIQUE(module, permission)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                UNIQUE(role_id, permission_id),
                FOREIGN KEY(role_id) REFERENCES roles(id),
                FOREIGN KEY(permission_id) REFERENCES permissions(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS modules(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE DEFAULT '',
                name TEXT NOT NULL,
                parent_id INTEGER NOT NULL DEFAULT 0,
                path TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                is_menu INTEGER NOT NULL DEFAULT 1
            )
        """)

        columns2 = [r["name"] for r in conn.execute("PRAGMA table_info(modules)").fetchall()]
        if "is_menu" not in columns2:
            conn.execute("ALTER TABLE modules ADD COLUMN is_menu INTEGER NOT NULL DEFAULT 1")

        if "parent_code" in columns2:
            pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_roles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                UNIQUE(user_id, role_id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(role_id) REFERENCES roles(id)
            )
        """)

        role_count = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
        if role_count == 0:
            conn.execute(
                "INSERT INTO roles(name, code, description, is_system, status) VALUES(?, ?, ?, ?, ?)",
                ("超级管理员", "super_admin", "系统默认超级管理员角色，拥有所有权限", 1, 1)
            )
            conn.execute(
                "INSERT INTO roles(name, code, description, is_system, status) VALUES(?, ?, ?, ?, ?)",
                ("普通管理员", "admin", "普通管理员角色", 0, 1)
            )

        mod_count = conn.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        if mod_count == 0:
            mods = [
                ("home", "首页", 0, "/admin/home", 0),
                ("system", "系统管理", 0, "", 1),
                ("system_user", "用户管理", 2, "/admin/user", 0),
                ("system_role", "角色管理", 2, "/admin/role", 1),
                ("system_func", "功能管理", 2, "/admin/function", 2),
                ("lookout", "智能瞭望", 0, "", 2),
                ("lookout_manage", "瞭源管理", 6, "/admin/lookout-manage", 0),
                ("lookout_collect", "瞭望采集", 6, "/admin/lookout-collect", 1),
                ("model", "模型管理", 0, "", 3),
                ("model_engine", "模型引擎", 9, "/admin/model", 0),
                ("data", "数据管理", 0, "", 4),
                ("data_warehouse", "数据仓库", 11, "/admin/data-warehouse", 0),
                ("settings", "系统设置", 0, "", 5),
                ("settings_config", "系统配置", 13, "/admin/system-config", 0),
                ("settings_audit", "日志与审计", 13, "/admin/audit", 1),
            ]
            for code, name, pid, path, sort in mods:
                conn.execute(
                    "INSERT INTO modules(code, name, parent_id, path, sort_order) VALUES(?, ?, ?, ?, ?)",
                    (code, name, pid, path, sort)
                )

        admin_user = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if admin_user:
            admin_role = conn.execute("SELECT id FROM roles WHERE name = ?", ("超级管理员",)).fetchone()
            if admin_role:
                existing = conn.execute(
                    "SELECT COUNT(*) FROM user_roles WHERE user_id = ? AND role_id = ?",
                    (admin_user["id"], admin_role["id"])
                ).fetchone()[0]
                if existing == 0:
                    conn.execute(
                        "INSERT INTO user_roles(user_id, role_id) VALUES(?, ?)",
                        (admin_user["id"], admin_role["id"])
                    )


class RoleRepository:
    @staticmethod
    def get_all():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM roles ORDER BY id").fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(role_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_list(page=1, page_size=20, keyword="", status=""):
        offset = (page - 1) * page_size
        conditions = []
        params = []
        if keyword:
            conditions.append("(name like ? or code like ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if status != "":
            conditions.append("status = ?")
            params.append(int(status))
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        with get_connection() as conn:
            total = conn.execute(f"SELECT count(*) FROM roles{where}", params).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM roles{where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
        return {"data": [dict(r) for r in rows], "total": total}

    @staticmethod
    def create(name, code, description="", status=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO roles(name, code, description, status) VALUES(?, ?, ?, ?)",
                    (name, code, description, status)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(role_id, name, code, description="", status=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE roles SET name=?, code=?, description=?, status=? WHERE id=?",
                    (name, code, description, status, role_id)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(role_id):
        role = RoleRepository.get_by_id(role_id)
        if role and role.get("is_system"):
            return False, "系统角色不能删除"
        with get_connection() as conn:
            conn.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
            conn.execute("DELETE FROM user_roles WHERE role_id = ?", (role_id,))
            cursor = conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))
            return cursor.rowcount > 0, ""

    @staticmethod
    def assign_permissions(role_id, permission_ids):
        with get_connection() as conn:
            conn.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
            for pid in permission_ids:
                conn.execute(
                    "INSERT INTO role_permissions(role_id, permission_id) VALUES(?, ?)",
                    (role_id, int(pid))
                )
        return True

    @staticmethod
    def get_role_permissions(role_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT permission_id FROM role_permissions WHERE role_id = ?",
                (role_id,)
            ).fetchall()
            return [r["permission_id"] for r in rows]

    @staticmethod
    def get_by_name(name):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM roles WHERE name = ?", (name,)).fetchone()
            return dict(row) if row else None


class PermissionRepository:
    @staticmethod
    def get_all():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM permissions ORDER BY id").fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_modules_tree():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM modules ORDER BY sort_order, id").fetchall()
            all_mods = [dict(r) for r in rows]
        tree = []
        lookup = {}
        for m in all_mods:
            m["children"] = []
            lookup[m["id"]] = m
        for m in all_mods:
            if m["parent_id"] == 0:
                tree.append(m)
            else:
                parent = lookup.get(m["parent_id"])
                if parent:
                    parent["children"].append(m)
        return tree

    @staticmethod
    def get_module_by_id(mid):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM modules WHERE id = ?", (mid,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create_module(name, code, parent_id=0, path="", sort_order=0):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO modules(name, code, parent_id, path, sort_order) VALUES(?, ?, ?, ?, ?)",
                    (name, code, parent_id, path, sort_order)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update_module(mid, name, code, parent_id=0, path="", sort_order=0):
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE modules SET name=?, code=?, parent_id=?, path=?, sort_order=? WHERE id=?",
                    (name, code, parent_id, path, sort_order, mid)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete_module(mid):
        with get_connection() as conn:
            children = conn.execute("SELECT COUNT(*) FROM modules WHERE parent_id = ?", (mid,)).fetchone()[0]
            if children > 0:
                return False, "请先删除子节点"
            cursor = conn.execute("DELETE FROM modules WHERE id = ?", (mid,))
            return cursor.rowcount > 0, ""


class ModuleRepository:
    @staticmethod
    def get_all():
        return PermissionRepository.get_modules_tree()

    @staticmethod
    def get_module_permissions_tree():
        modules = []
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM modules ORDER BY sort_order, id").fetchall()
        for r in rows:
            d = dict(r)
            d["permission_id"] = "mod_" + str(d["id"])
            modules.append(d)
        return modules


class UserRoleRepository:
    @staticmethod
    def get_user_role_names(user_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT r.name FROM user_roles ur JOIN roles r ON ur.role_id = r.id WHERE ur.user_id = ?",
                (user_id,)
            ).fetchall()
            return [r["name"] for r in rows]

    @staticmethod
    def assign_roles(user_id, role_ids):
        with get_connection() as conn:
            conn.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
            for rid in role_ids:
                if rid:
                    conn.execute(
                        "INSERT INTO user_roles(user_id, role_id) VALUES(?, ?)",
                        (user_id, int(rid))
                    )
        return True
