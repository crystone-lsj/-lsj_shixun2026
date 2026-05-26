import json
import tornado.web

from app.controllers.base import AdminBaseHandler
from app.models.user import UserRepository
from app.models.role import RoleRepository


class AdminUserListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/user.html", title="用户管理")


class AdminUserApiListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 20))
        keyword = (self.get_argument("keyword", "") or "").strip()
        status = self.get_argument("status", "")
        result = UserRepository.get_user_list(page=page, page_size=limit, keyword=keyword, status=status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "msg": "", "count": result["total"], "data": result["data"]}))


class AdminUserApiAddHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        username = self.get_body_argument("username", "").strip()
        nickname = self.get_body_argument("nickname", "").strip()
        email = self.get_body_argument("email", "").strip()
        password = self.get_body_argument("password", "").strip()
        status = int(self.get_body_argument("status", 1))
        role_ids = self.get_arguments("role_ids")

        if not username or not password:
            return self._json(1, "用户名和密码不能为空")
        if UserRepository.username_exists(username):
            return self._json(1, "用户名已存在")

        from app.models.role import UserRoleRepository
        if UserRepository.create_user(username, password, nickname, email, status):
            user = UserRepository.get_user_by_username(username)
            if user and role_ids:
                UserRoleRepository.assign_roles(user["id"], role_ids)
            return self._json(0, "添加成功")
        return self._json(1, "添加失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminUserApiUpdateHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        user_id = int(self.get_body_argument("id", 0))
        username = self.get_body_argument("username", "").strip()
        nickname = self.get_body_argument("nickname", "").strip()
        email = self.get_body_argument("email", "").strip()
        password = self.get_body_argument("password", "").strip()
        status = int(self.get_body_argument("status", 1))
        role_ids = self.get_arguments("role_ids")

        from app.models.role import UserRoleRepository
        if UserRepository.username_exists(username, exclude_id=user_id):
            return self._json(1, "用户名已存在")

        if UserRepository.update_user(user_id, username, nickname, email, password, status):
            if role_ids is not None:
                UserRoleRepository.assign_roles(user_id, role_ids)
            return self._json(0, "更新成功")
        return self._json(1, "更新失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminUserApiDeleteHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
            ids = [int(i) for i in body.get("ids", [])]
        except Exception:
            ids = []

        if not ids:
            return self._json(1, "请选择要删除的用户")

        current_user = self.get_current_user()
        if current_user == "admin" and "admin" in ids:
            current = UserRepository.get_user_by_username("admin")
            if current and current["id"] in ids:
                return self._json(1, "不能删除超级管理员账号")

        count = UserRepository.delete_users(ids)
        if count > 0:
            return self._json(0, f"成功删除 {count} 个用户")
        return self._json(1, "删除失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminUserApiRolesHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        roles = RoleRepository.get_all()
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": roles}))
