import json
import tornado.web
from app.controllers.base import AdminBaseHandler
from app.models.role import ModuleRepository
from app.models.lookout import LookoutSourceRepository


class AdminIndexHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/index.html", title="智能瞭望与问数系统")


class HomeHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/home.html", title="首页")


class LookoutManageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/lookout-manage.html", title="瞭源管理")


class LookoutCollectHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/lookout-collect.html", title="瞭望采集")


class DataWarehouseHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/data-warehouse.html", title="数据仓库")


class DigitalEmployeeHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/digital-employee-manage.html", title="数字员工")


class DataScreenHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/data-screen.html", title="数智大屏")


class SystemStatsHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/system-stats.html", title="系统统计")


class SystemConfigHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/system-config.html", title="系统配置")


class AuditHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/audit.html", title="日志审计")
