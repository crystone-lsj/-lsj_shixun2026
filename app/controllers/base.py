# Controller 公共基础类 (BaseHandler)
"""
在tornado中
- 每一个Ur1对应一个RequestHandler 可以理解为Controller
- RequestHandler 提供 post/get 等方法来处理http请求

本程序可以提供一个统一的基础类,用于处理一些公共业务,如登录态的处理或获得逻辑,供其他Handler继承使用
"""
import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        if uid:
            return uid.decode("utf-8")
        username = self.get_secure_cookie("username")
        if username:
            return username.decode("utf-8")
        return None

class AdminBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("admin_username")
        if not username:
            return None
        return username.decode("utf-8")