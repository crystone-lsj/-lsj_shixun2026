import json
import tornado.web

from app.controllers.base import AdminBaseHandler
from app.models.role import PermissionRepository


class AdminFunctionHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/function.html", title="功能管理")


class AdminFunctionApiListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        tree = PermissionRepository.get_modules_tree()
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": tree}))


class AdminFunctionApiAddHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        name = self.get_body_argument("name", "").strip()
        code = self.get_body_argument("code", "").strip()
        parent_id = int(self.get_body_argument("parent_id", 0))
        path = self.get_body_argument("path", "").strip()
        sort_order = int(self.get_body_argument("sort_order", 0))

        if not name or not code:
            return self._json(1, "功能名称和标识不能为空")

        if PermissionRepository.create_module(name, code, parent_id, path, sort_order):
            return self._json(0, "添加成功")
        return self._json(1, "添加失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminFunctionApiUpdateHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        mid = int(self.get_body_argument("id", 0))
        name = self.get_body_argument("name", "").strip()
        code = self.get_body_argument("code", "").strip()
        parent_id = int(self.get_body_argument("parent_id", 0))
        path = self.get_body_argument("path", "").strip()
        sort_order = int(self.get_body_argument("sort_order", 0))

        if not name or not code:
            return self._json(1, "功能名称和标识不能为空")

        if PermissionRepository.update_module(mid, name, code, parent_id, path, sort_order):
            return self._json(0, "更新成功")
        return self._json(1, "更新失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminFunctionApiDeleteHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        mid = int(self.get_body_argument("id", 0))
        success, msg = PermissionRepository.delete_module(mid)
        if success:
            return self._json(0, "删除成功")
        return self._json(1, msg or "删除失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminFunctionApiParentsHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        tree = PermissionRepository.get_modules_tree()
        options = [{"id": 0, "name": "顶级节点"}]

        def flatten(nodes):
            for n in nodes:
                options.append({"id": n["id"], "name": n["name"]})
                if n.get("children"):
                    flatten(n["children"])

        flatten(tree)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": options}))


class SystemConfigHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/system-config.html", title="系统配置")

    @tornado.web.authenticated
    def post(self):
        self._json(0, "系统配置已保存")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AuditHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/audit.html", title="日志与审计")
