import json
import tornado.web
import asyncio
from app.controllers.base import AdminBaseHandler
from app.models.lookout import LookoutSourceRepository, LookoutDataRepository
from app.models.collector import run_collection


class LookoutManageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/lookout-manage.html", title="瞭源管理")


class LookoutCollectHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        sources = LookoutSourceRepository.get_all()
        self.render("admin/lookout-collect.html", sources=sources, title="瞭望采集")


class LookoutSourceListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        sources = LookoutSourceRepository.get_all()
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": sources}))


class LookoutSourceAddHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        name = self.get_body_argument("name", "").strip()
        url_template = self.get_body_argument("url_template", "").strip()
        headers_str = self.get_body_argument("headers", "{}")
        param_fields_str = self.get_body_argument("param_fields", "[]")
        selector_title = self.get_body_argument("selector_title", "")
        selector_content = self.get_body_argument("selector_content", "")
        selector_time = self.get_body_argument("selector_time", "")
        selector_source = self.get_body_argument("selector_source", "")
        enabled = int(self.get_body_argument("enabled", 1))

        if not name or not url_template:
            return self._json(1, "名称和URL不能为空")

        if LookoutSourceRepository.create(name, url_template, headers_str, param_fields_str,
                                          selector_title, selector_content, selector_time, selector_source, enabled):
            return self._json(0, "添加成功")
        return self._json(1, "名称已存在")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class LookoutSourceUpdateHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        sid = int(self.get_body_argument("id", 0))
        name = self.get_body_argument("name", "").strip()
        url_template = self.get_body_argument("url_template", "").strip()
        headers_str = self.get_body_argument("headers", "{}")
        param_fields_str = self.get_body_argument("param_fields", "[]")
        selector_title = self.get_body_argument("selector_title", "")
        selector_content = self.get_body_argument("selector_content", "")
        selector_time = self.get_body_argument("selector_time", "")
        selector_source = self.get_body_argument("selector_source", "")
        enabled = int(self.get_body_argument("enabled", 1))

        if not name or not url_template:
            return self._json(1, "名称和URL不能为空")

        if LookoutSourceRepository.update(sid, name, url_template, headers_str, param_fields_str,
                                          selector_title, selector_content, selector_time, selector_source, enabled):
            return self._json(0, "更新成功")
        return self._json(1, "更新失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class LookoutSourceDeleteHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        sid = int(self.get_body_argument("id", 0))
        if LookoutSourceRepository.delete(sid):
            return self._json(0, "删除成功")
        return self._json(1, "删除失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class LookoutCollectRunHandler(AdminBaseHandler):
    @tornado.web.authenticated
    async def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
            source_ids = body.get("source_ids", [])
            keywords = body.get("keywords", "").split(",")
            keywords = [k.strip() for k in keywords if k.strip()]
            pages = int(body.get("pages", 1))

            if not source_ids or not keywords:
                return self._json(1, "请选择采集源并输入关键字")

            result = await run_collection(source_ids, keywords, pages=pages)
            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.write(json.dumps({"code": 0, "msg": f"采集完成，共获取 {result['saved']} 条数据", "data": result}))
        except Exception as e:
            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.write(json.dumps({"code": 1, "msg": f"采集异常: {str(e)}"}))

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class LookoutDataListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 20))
        keyword = (self.get_argument("keyword", "") or "").strip()

        result = LookoutDataRepository.get_list(page=page, page_size=limit, keyword=keyword)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": result}))


class LookoutDataDeleteHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            body = json.loads(self.request.body.decode("utf-8"))
            ids = body.get("ids", [])
        except Exception:
            ids = []

        if not ids:
            return self._json(1, "请选择要删除的数据")

        count = LookoutDataRepository.delete([int(i) for i in ids])
        if count > 0:
            return self._json(0, f"成功删除 {count} 条数据")
        return self._json(1, "删除失败")

    def _json(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))
