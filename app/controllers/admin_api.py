import json
import tornado.web

from app.controllers.base import AdminBaseHandler
from app.models.api_service import ApiServiceRepository


class ApiManageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/api-manage.html", title="接口管理")


class ApiManageListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 20))
        keyword = (self.get_argument("keyword", "") or "").strip()
        category = (self.get_argument("category", "") or "").strip()
        status = self.get_argument("status", "")
        result = ApiServiceRepository.get_list(page=page, page_size=limit, keyword=keyword, category=category, status=status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "msg": "", "count": result["total"], "data": result["data"]}))


class ApiManageAddHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        name = self.get_body_argument("name", "").strip()
        url = self.get_body_argument("url", "").strip()
        method = self.get_body_argument("method", "GET").strip()
        response_format = self.get_body_argument("response_format", "JSON").strip()
        qps = self.get_body_argument("qps", "").strip()
        description = self.get_body_argument("description", "").strip()
        category = self.get_body_argument("category", "").strip()
        token_required = int(self.get_body_argument("token_required", 0))
        status = int(self.get_body_argument("status", 1))
        example_response = self.get_body_argument("example_response", "").strip()

        if not name or not url:
            return self._json(1, "接口名称和地址不能为空")

        if ApiServiceRepository.create(name, url, method, response_format, qps, description,
                                       category, token_required, status, example_response):
            return self._json(0, "添加成功")
        return self._json(1, "添加失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class ApiManageUpdateHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        api_id = int(self.get_body_argument("id", 0))
        name = self.get_body_argument("name", "").strip()
        url = self.get_body_argument("url", "").strip()
        method = self.get_body_argument("method", "GET").strip()
        response_format = self.get_body_argument("response_format", "JSON").strip()
        qps = self.get_body_argument("qps", "").strip()
        description = self.get_body_argument("description", "").strip()
        category = self.get_body_argument("category", "").strip()
        token_required = int(self.get_body_argument("token_required", 0))
        status = int(self.get_body_argument("status", 1))
        example_response = self.get_body_argument("example_response", "").strip()

        if not name or not url:
            return self._json(1, "接口名称和地址不能为空")

        if ApiServiceRepository.update(api_id, name, url, method, response_format, qps, description,
                                       category, token_required, status, example_response):
            return self._json(0, "更新成功")
        return self._json(1, "更新失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class ApiManageDeleteHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        api_id = int(self.get_body_argument("id", 0))
        if ApiServiceRepository.delete(api_id):
            return self._json(0, "删除成功")
        return self._json(1, "删除失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class ApiManageCategoriesHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        categories = ApiServiceRepository.get_categories()
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": categories}))
