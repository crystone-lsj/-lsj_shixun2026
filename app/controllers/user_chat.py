import json
import tornado.web
import asyncio
import httpx

from app.controllers.base import BaseHandler
from app.models.frontend_user import FrontendUserRepository, ChatSessionRepository, ChatMessageRepository
from app.models.digital_employee import DigitalEmployeeRepository


class UserLoginHandler(BaseHandler):
    def get(self):
        self.render("user/login.html", title="登录 - 智能瞭问数系统", error=None)

    def post(self):
        username = (self.get_body_argument("username", "") or "").strip()
        password = self.get_body_argument("password", "")
        if not username or not password:
            return self.render("user/login.html", title="登录 - 智能瞭望与问数系统", error="用户名或密码不能为空")
        user = FrontendUserRepository.verify_user(username, password)
        if not user:
            return self.render("user/login.html", title="登录 - 智能瞭望与问数系统", error="用户名或密码错误")
        if user["status"] != 1:
            return self.render("user/login.html", title="登录 - 智能瞭望与问数系统", error="账号已被禁用")
        self.set_secure_cookie("user_id", str(user["id"]))
        self.set_secure_cookie("user_name", user["username"])
        self.redirect("/chat")


class UserRegisterHandler(BaseHandler):
    def get(self):
        self.render("user/register.html", title="注册 - 智能瞭望与问数系统", error=None)

    def post(self):
        username = (self.get_body_argument("username", "") or "").strip()
        password = self.get_body_argument("password", "")
        confirm = self.get_body_argument("confirm", "")
        nickname = (self.get_body_argument("nickname", "") or "").strip()
        if not username or not password:
            return self.render("user/register.html", title="注册 - 智能瞭望与问数系统", error="用户名和密码不能为空")
        if password != confirm:
            return self.render("user/register.html", title="注册 - 智能瞭望与问数系统", error="两次密码输入不一致")
        if len(password) < 6:
            return self.render("user/register.html", title="注册 - 智能瞭望与问数系统", error="密码长度不能少于6位")
        if FrontendUserRepository.create_user(username, password, nickname):
            self.redirect("/user/login")
        else:
            return self.render("user/register.html", title="注册 - 智能瞭望与问数系统", error="用户名已存在")


class UserLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user_id")
        self.clear_cookie("user_name")
        self.redirect("/user/login")


class ChatIndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = int(self.get_secure_cookie("user_id"))
        employees = DigitalEmployeeRepository.get_all_active()
        from app.models.model import ModelRepository
        result = ModelRepository.get_all(page=1, page_size=100)
        models = result["data"]
        sessions = ChatSessionRepository.get_sessions(user_id)
        default_model_id = None
        for m in models:
            if m.get("is_default"):
                default_model_id = m["id"]
                break
        user = FrontendUserRepository.get_user_by_id(user_id)
        display_name = user.get("nickname") or user.get("username") if user else "用户"
        self.render("user/chat.html", title="智能对话",
                    current_user=display_name,
                    employees=employees, models=models, sessions=sessions,
                    default_model_id=default_model_id,
                    employees_json=json.dumps(employees, ensure_ascii=False))


class ChatApiSessionsHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = int(self.get_secure_cookie("user_id"))
        sessions = ChatSessionRepository.get_sessions(user_id)
        self.write(json.dumps({"code": 0, "data": sessions}))

    @tornado.web.authenticated
    def post(self):
        user_id = int(self.get_secure_cookie("user_id"))
        title = self.get_body_argument("title", "新对话")
        model_id = int(self.get_body_argument("model_id", 0) or 0)
        sid = ChatSessionRepository.create(user_id, title, model_id if model_id else None)
        self.write(json.dumps({"code": 0, "data": {"id": sid}}))

    @tornado.web.authenticated
    def delete(self):
        user_id = int(self.get_secure_cookie("user_id"))
        sid = int(self.get_argument("id", 0))
        if ChatSessionRepository.delete(sid, user_id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))


class ChatApiMessagesHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = int(self.get_secure_cookie("user_id"))
        sid = int(self.get_argument("session_id", 0))
        session = ChatSessionRepository.get_session(sid, user_id)
        if not session:
            return self.write(json.dumps({"code": 1, "msg": "会话不存在"}))
        messages = ChatMessageRepository.get_messages(sid)
        self.write(json.dumps({"code": 0, "data": messages}))


class ChatApiStreamHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        user_id = int(self.get_secure_cookie("user_id"))
        body = json.loads(self.request.body.decode("utf-8"))
        session_id = int(body.get("session_id", 0))
        content = body.get("content", "").strip()
        model_id = int(body.get("model_id", 0) or 0)
        employee_alias = body.get("employee_alias", "")

        if not content:
            self.write(json.dumps({"code": 1, "msg": "请输入内容"}))
            return

        session = ChatSessionRepository.get_session(session_id, user_id) if session_id else None

        if not session:
            title = content[:20] + ("..." if len(content) > 20 else "")
            session_id = ChatSessionRepository.create(user_id, title, model_id if model_id else None)
            session = ChatSessionRepository.get_session(session_id, user_id)

        ChatMessageRepository.add(session_id, "user", content, employee_alias=employee_alias)

        if employee_alias:
            emp = DigitalEmployeeRepository.get_by_alias(employee_alias)
            if emp and emp["category"] == "ai":
                self.set_header("Content-Type", "text/event-stream")
                self.set_header("Cache-Control", "no-cache")
                self.set_header("Connection", "keep-alive")
                await self._stream_ai_response(session_id, content, emp)
                return
            elif emp and emp["category"] == "normal":
                await self._handle_normal_employee(session_id, content, emp)
                return

        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        await self._stream_ai_response(session_id, content, None)

    async def _stream_ai_response(self, session_id, content, emp):
        from app.models.model import ModelRepository
        result = ModelRepository.get_all(page=1, page_size=100)
        models = result["data"]
        model = None
        for m in models:
            if m.get("is_default"):
                model = m
                break
        if not model and models:
            model = models[0]
        if not model:
            self.write("data: " + json.dumps({"done": True, "content": "未配置可用模型"}) + "\n\n")
            await self.flush()
            return

        prompt = ""
        if emp:
            prompt = emp.get("prompt", "")

        api_key = model.get("api_key", "")
        api_url = model.get("api_url", "").rstrip("/")
        model_name = model.get("model_code", model.get("name", ""))

        messages = [{"role": "user", "content": content}]
        if prompt:
            messages = [{"role": "system", "content": prompt}, {"role": "user", "content": content}]

        full_content = ""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", f"{api_url}/chat/completions",
                    json={"model": model_name, "messages": messages, "stream": True},
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                delta_content = delta.get("content", "")
                                if delta_content:
                                    full_content += delta_content
                                    self.write("data: " + json.dumps({"content": delta_content, "done": False}) + "\n\n")
                                    await self.flush()
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            full_content = f"请求失败: {str(e)}"
            self.write("data: " + json.dumps({"content": full_content, "done": True}) + "\n\n")
            await self.flush()

        ChatMessageRepository.add(session_id, "assistant", full_content, model.get("name", ""))
        self.write("data: " + json.dumps({"done": True}) + "\n\n")
        await self.flush()

    async def _handle_normal_employee(self, session_id, content, emp):
        import re
        config = json.loads(emp.get("config", "{}"))
        api_id = emp.get("api_id")
        result = ""

        if api_id:
            from app.models.api_service import ApiServiceRepository
            api = ApiServiceRepository.get_by_id(api_id)
            if api:
                url = api["url"]
                if api["method"] == "GET":
                    param_name = config.get("api_param", "keyword")
                    value = re.sub(r"^@" + emp["alias"] + r"\s*", "", content).strip()
                    if param_name and value:
                        sep = "&" if "?" in url else "?"
                        url = f"{url}{sep}{param_name}={value}"
                    try:
                        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                            resp = await client.get(url)
                            result = resp.text
                    except Exception as e:
                        result = f"请求失败: {str(e)}"
        else:
            result = f"该员工({emp['name']})暂未配置API服务"

        ChatMessageRepository.add(session_id, "assistant", result, employee_alias=emp["alias"])
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.write("data: " + json.dumps({"content": result, "done": True}) + "\n\n")
        await self.flush()
