import json
import tornado.web
import tornado.gen
from app.controllers.base import AdminBaseHandler
from app.models.model import ModelRepository, call_model_api


class AdminModelHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/model.html", title="模型引擎", current_user=self.current_user)


class AdminModelListHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("limit", 6))
        result = ModelRepository.get_all(page=page, page_size=page_size)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "msg": "", "data": result}))


class AdminModelAddHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        name = self.get_body_argument("name", "").strip()
        api_url = self.get_body_argument("api_url", "").strip()
        api_key = self.get_body_argument("api_key", "").strip()
        model_code = self.get_body_argument("model_code", "").strip()
        max_tokens = int(self.get_body_argument("max_tokens", 4096))
        temperature = float(self.get_body_argument("temperature", 0.7))

        if not name or not api_url or not api_key or not model_code:
            return self._json_response(1, "参数不完整")

        if ModelRepository.create(name, api_url, api_key, model_code, max_tokens, temperature):
            return self._json_response(0, "添加成功")
        return self._json_response(1, "模型名称已存在")

    def _json_response(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminModelUpdateHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        mid = int(self.get_body_argument("id", 0))
        name = self.get_body_argument("name", "").strip()
        api_url = self.get_body_argument("api_url", "").strip()
        api_key = self.get_body_argument("api_key", "").strip()
        model_code = self.get_body_argument("model_code", "").strip()
        max_tokens = int(self.get_body_argument("max_tokens", 4096))
        temperature = float(self.get_body_argument("temperature", 0.7))
        enabled = int(self.get_body_argument("enabled", 1))

        if not name or not api_url or not model_code:
            return self._json_response(1, "参数不完整")

        existing = ModelRepository.get_by_id(mid)
        if not api_key and existing:
            api_key = existing.get("api_key", "")

        if ModelRepository.update(mid, name, api_url, api_key, model_code, max_tokens, temperature, enabled):
            return self._json_response(0, "更新成功")
        return self._json_response(1, "更新失败")

    def _json_response(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminModelDeleteHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        mid = int(self.get_body_argument("id", 0))
        if ModelRepository.delete(mid):
            return self._json_response(0, "删除成功")
        return self._json_response(1, "删除失败")

    def _json_response(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminModelSetDefaultHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def post(self):
        mid = int(self.get_body_argument("id", 0))
        ModelRepository.set_default(mid)
        return self._json_response(0, "设置成功")

    def _json_response(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminModelChatHandler(AdminBaseHandler):
    @tornado.web.authenticated
    async def post(self):
        mid = int(self.get_argument("id", 0))
        model = ModelRepository.get_by_id(mid)
        if not model:
            return self._json_response(1, "模型不存在")

        body = json.loads(self.request.body.decode("utf-8"))
        messages = body.get("messages", [])
        stream = body.get("stream", False)

        if stream:
            self.set_header("Content-Type", "text/event-stream")
            self.set_header("Cache-Control", "no-cache")
            self.set_header("Connection", "keep-alive")

            full_content = ""
            try:
                async for chunk in call_model_api(
                    model["api_url"], model["api_key"], model["model_code"],
                    messages, stream=True, max_tokens=model["max_tokens"], temperature=model["temperature"]
                ):
                    if isinstance(chunk, dict) and "usage" in chunk:
                        u = chunk["usage"]
                        prompt_t = u.get("prompt_tokens", 0)
                        comp_t = u.get("completion_tokens", 0)
                        ModelRepository.update_stats(mid, prompt_t, comp_t)
                        ModelRepository.add_chat(mid, messages, prompt_t, comp_t, "success")
                        self.write(f"data: {json.dumps({'usage': u})}\n\n")
                        await self.flush()
                    else:
                        full_content += str(chunk)
                        self.write(f"data: {json.dumps({'content': chunk})}\n\n")
                        await self.flush()
            except Exception as e:
                ModelRepository.add_chat(mid, messages, 0, 0, "error", str(e))
                self.write(f"data: {json.dumps({'error': str(e)})}\n\n")
                await self.flush()
            self.finish()
        else:
            self.set_header("Content-Type", "application/json; charset=utf-8")
            try:
                result = None
                async for r in call_model_api(
                    model["api_url"], model["api_key"], model["model_code"],
                    messages, stream=False, max_tokens=model["max_tokens"], temperature=model["temperature"]
                ):
                    result = r

                if result:
                    usage = result.get("usage", {})
                    prompt_t = usage.get("prompt_tokens", 0)
                    comp_t = usage.get("completion_tokens", 0)
                    ModelRepository.update_stats(mid, prompt_t, comp_t)
                    ModelRepository.add_chat(mid, messages, prompt_t, comp_t, "success")
                    self.write(json.dumps({"code": 0, "data": result}))
                else:
                    self.write(json.dumps({"code": 1, "msg": "调用失败"}))
            except Exception as e:
                ModelRepository.add_chat(mid, messages, 0, 0, "error", str(e))
                self.write(json.dumps({"code": 1, "msg": str(e)}))

    def _json_response(self, code, msg):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": code, "msg": msg}))


class AdminModelStatsHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        mid = int(self.get_argument("id", 0))
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("limit", 20))
        history = ModelRepository.get_chat_history(mid, page=page, page_size=page_size)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"code": 0, "data": history}))
