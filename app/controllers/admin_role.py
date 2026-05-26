import json
import tornado.web

from app.controllers.base import AdminBaseHandler
from app.models.role import RoleRepository, PermissionRepository


class AdminRoleListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/role.html", title="角色管理")


class AdminRoleApiListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 20))
        keyword = (self.get_argument("keyword", "") or "").strip()
        status = self.get_argument("status", "")
        result = RoleRepository.get_list(page=page, page_size=limit, keyword=keyword, status=status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "msg": "", "count": result["total"], "data": result["data"]}))


class AdminRoleApiAddHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        name = self.get_body_argument("name", "").strip()
        code = self.get_body_argument("code", "").strip()
        description = self.get_body_argument("description", "").strip()
        status = int(self.get_body_argument("status", 1))
        permission_ids = self.get_arguments("permission_ids")

        if not name or not code:
            return self._json(1, "角色名称和标识不能为空")
        if RoleRepository.create(name, code, description, status):
            role = RoleRepository.get_by_name(name)
            if role and permission_ids:
                RoleRepository.assign_permissions(role["id"], permission_ids)
            return self._json(0, "添加成功")
        return self._json(1, "角色名称或标识已存在")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminRoleApiUpdateHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        role_id = int(self.get_body_argument("id", 0))
        name = self.get_body_argument("name", "").strip()
        code = self.get_body_argument("code", "").strip()
        description = self.get_body_argument("description", "").strip()
        status = int(self.get_body_argument("status", 1))
        permission_ids = self.get_arguments("permission_ids")

        if not name or not code:
            return self._json(1, "角色名称和标识不能为空")
        if RoleRepository.update(role_id, name, code, description, status):
            if permission_ids is not None:
                RoleRepository.assign_permissions(role_id, permission_ids)
            return self._json(0, "更新成功")
        return self._json(1, "更新失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminRoleApiDeleteHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        role_id = int(self.get_body_argument("id", 0))
        success, msg = RoleRepository.delete(role_id)
        if success:
            return self._json(0, "删除成功")
        return self._json(1, msg or "删除失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminRoleApiPermissionsHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        tree = PermissionRepository.get_modules_tree()
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": tree}))


class AdminRoleApiRolePermsHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        role_id = int(self.get_argument("role_id", 0))
        perms = RoleRepository.get_role_permissions(role_id)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": perms}))
