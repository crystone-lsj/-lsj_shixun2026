import json
import tornado.web

from app.controllers.base import AdminBaseHandler
from app.models.digital_employee import DigitalEmployeeRepository


class DigitalEmployeeManageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/digital-employee-manage.html", title="数字员工")


class DigitalEmployeeListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 20))
        keyword = (self.get_argument("keyword", "") or "").strip()
        category = (self.get_argument("category", "") or "").strip()
        status = self.get_argument("status", "")
        result = DigitalEmployeeRepository.get_list(page=page, page_size=limit, keyword=keyword, category=category, status=status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "msg": "", "count": result["total"], "data": result["data"]}))


class DigitalEmployeeAddHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        name = self.get_body_argument("name", "").strip()
        alias = self.get_body_argument("alias", "").strip()
        category = self.get_body_argument("category", "normal").strip()
        description = self.get_body_argument("description", "").strip()
        prompt = self.get_body_argument("prompt", "").strip()
        api_id = int(self.get_body_argument("api_id", 0) or 0)
        icon = self.get_body_argument("icon", "").strip()
        color = self.get_body_argument("color", "#6366f1").strip()
        status = int(self.get_body_argument("status", 1))
        config = self.get_body_argument("config", "{}").strip()

        if not name or not alias:
            return self._json(1, "名称和别名不能为空")

        if DigitalEmployeeRepository.create(name, alias, category, description, config, prompt,
                                             api_id if api_id else None, icon, color, status):
            return self._json(0, "添加成功")
        return self._json(1, "别名已存在")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class DigitalEmployeeUpdateHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        emp_id = int(self.get_body_argument("id", 0))
        name = self.get_body_argument("name", "").strip()
        alias = self.get_body_argument("alias", "").strip()
        category = self.get_body_argument("category", "normal").strip()
        description = self.get_body_argument("description", "").strip()
        prompt = self.get_body_argument("prompt", "").strip()
        api_id = int(self.get_body_argument("api_id", 0) or 0)
        icon = self.get_body_argument("icon", "").strip()
        color = self.get_body_argument("color", "#6366f1").strip()
        status = int(self.get_body_argument("status", 1))
        config = self.get_body_argument("config", "{}").strip()

        if not name or not alias:
            return self._json(1, "名称和别名不能为空")

        if DigitalEmployeeRepository.update(emp_id, name, alias, category, description, config, prompt,
                                             api_id if api_id else None, icon, color, status):
            return self._json(0, "更新成功")
        return self._json(1, "别名已存在")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class DigitalEmployeeDeleteHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        emp_id = int(self.get_body_argument("id", 0))
        if DigitalEmployeeRepository.delete(emp_id):
            return self._json(0, "删除成功")
        return self._json(1, "删除失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class DigitalEmployeeAllHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        employees = DigitalEmployeeRepository.get_all_active()
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": employees}))
