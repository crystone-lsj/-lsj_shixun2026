import tornado.web
import json

from app.controllers.base import AdminBaseHandler
from app.models.user import UserRepository


class AdminLoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("admin/login.html", title="AI智能瞭望系统 - 管理员登录", error=None)

    def post(self):
        username = (self.get_body_argument("username", "") or "").strip()
        password = self.get_body_argument("password", "")

        if not username or not password:
            return self.render(
                "admin/login.html",
                title="AI智能瞭望系统 - 管理员登录",
                error="用户名或密码不能为空"
            )

        if not UserRepository.verify_user(username, password):
            return self.render(
                "admin/login.html",
                title="AI智能瞭望系统 - 管理员登录",
                error="用户名或密码错误"
            )

        user = UserRepository.get_user_by_username(username)
        if user:
            UserRepository.update_login_time(user["id"])
        self.set_secure_cookie("admin_username", username)
        self.redirect("/admin")


class AdminLogoutHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("admin_username")
        self.redirect("/admin/login")
