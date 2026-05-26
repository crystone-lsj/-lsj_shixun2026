# 程序的主入口
# 承担服务器容器 + 程序作用
# 服务器容器: 提供 http 容器服务，程序放置于该容器中运行
# 程序: 智能瞭望与智能问数系统

import os
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer

# 引入 controller 层
from app.controllers.auth import LoginHandler, LogoutHandler
from app.controllers.home import IndexHandler
from app.controllers.admin_auth import AdminLoginHandler, AdminLogoutHandler
from app.controllers.admin_user import (
    AdminUserListHandler,
    AdminUserApiListHandler,
    AdminUserApiAddHandler,
    AdminUserApiUpdateHandler,
    AdminUserApiDeleteHandler,
    AdminUserApiRolesHandler
)
from app.controllers.admin_pages import (
    SystemConfigHandler,
    AuditHandler,
    AdminFunctionHandler,
    AdminFunctionApiListHandler,
    AdminFunctionApiAddHandler,
    AdminFunctionApiUpdateHandler,
    AdminFunctionApiDeleteHandler,
    AdminFunctionApiParentsHandler
)
from app.controllers.admin_nav import (
    AdminIndexHandler,
    HomeHandler,
    LookoutManageHandler,
    LookoutCollectHandler,
    DataWarehouseHandler,
    DigitalEmployeeHandler,
    DataScreenHandler,
    SystemStatsHandler
)
from app.controllers.admin_api import (
    ApiManageHandler,
    ApiManageListHandler,
    ApiManageAddHandler,
    ApiManageUpdateHandler,
    ApiManageDeleteHandler,
    ApiManageCategoriesHandler
)
from app.controllers.admin_digital_employee import (
    DigitalEmployeeManageHandler,
    DigitalEmployeeListHandler,
    DigitalEmployeeAddHandler,
    DigitalEmployeeUpdateHandler,
    DigitalEmployeeDeleteHandler,
    DigitalEmployeeAllHandler
)
from app.controllers.user_chat import (
    UserLoginHandler,
    UserRegisterHandler,
    UserLogoutHandler,
    ChatIndexHandler,
    ChatApiSessionsHandler,
    ChatApiMessagesHandler,
    ChatApiStreamHandler
)
from app.controllers.admin_lookout import (
    LookoutSourceListHandler,
    LookoutSourceAddHandler,
    LookoutSourceUpdateHandler,
    LookoutSourceDeleteHandler,
    LookoutCollectRunHandler,
    LookoutDataListHandler,
    LookoutDataDeleteHandler
)
from app.controllers.admin_role import (
    AdminRoleListHandler,
    AdminRoleApiListHandler,
    AdminRoleApiAddHandler,
    AdminRoleApiUpdateHandler,
    AdminRoleApiDeleteHandler,
    AdminRoleApiPermissionsHandler,
    AdminRoleApiRolePermsHandler
)
from app.controllers.admin_model import (
    AdminModelHandler,
    AdminModelListHandler,
    AdminModelAddHandler,
    AdminModelUpdateHandler,
    AdminModelDeleteHandler,
    AdminModelSetDefaultHandler,
    AdminModelChatHandler,
    AdminModelStatsHandler
)

# 引入数据库初始化方法
from app.models.db import init_db


def make_app():
    base_url = os.path.dirname(os.path.abspath(__file__))

    settings = dict(
        # 预留 view 层的配置
        template_path=os.path.join(base_url, "app", "templates"),
        static_path=os.path.join(base_url, "app", "static"),

        # cookie 配置
        cookie_secret="demp-cookie-secret-change-wayne",

        # 登录跳转地址
        login_url="/auth/login",

        # xsrf 防护（管理后台已有登录验证，暂关闭）
        xsrf_cookies=False,

        # 开发模式
        debug=True,
        autoreload=True
    )

    return tornado.web.Application([
        # 前台路由
        (r"/", IndexHandler),
        (r"/auth/login", LoginHandler),
        (r"/auth/logout", LogoutHandler),

        # 用户侧路由
        (r"/user/login", UserLoginHandler),
        (r"/user/register", UserRegisterHandler),
        (r"/user/logout", UserLogoutHandler),
        (r"/chat", ChatIndexHandler),
        (r"/api/chat/sessions", ChatApiSessionsHandler),
        (r"/api/chat/messages", ChatApiMessagesHandler),
        (r"/api/chat/stream", ChatApiStreamHandler),

        # 后台管理路由
        (r"/admin/login", AdminLoginHandler),
        (r"/admin/logout", AdminLogoutHandler),
        (r"/admin", AdminIndexHandler),

        # 首页
        (r"/admin/home", HomeHandler),

        # 系统管理
        (r"/admin/user", AdminUserListHandler),
        (r"/admin/api/user/list", AdminUserApiListHandler),
        (r"/admin/api/user/add", AdminUserApiAddHandler),
        (r"/admin/api/user/update", AdminUserApiUpdateHandler),
        (r"/admin/api/user/delete", AdminUserApiDeleteHandler),
        (r"/admin/api/user/roles", AdminUserApiRolesHandler),
        (r"/admin/role", AdminRoleListHandler),
        (r"/admin/api/role/list", AdminRoleApiListHandler),
        (r"/admin/api/role/add", AdminRoleApiAddHandler),
        (r"/admin/api/role/update", AdminRoleApiUpdateHandler),
        (r"/admin/api/role/delete", AdminRoleApiDeleteHandler),
        (r"/admin/api/role/permissions", AdminRoleApiPermissionsHandler),
        (r"/admin/api/role/roleperms", AdminRoleApiRolePermsHandler),
        (r"/admin/function", AdminFunctionHandler),
        (r"/admin/api/function/list", AdminFunctionApiListHandler),
        (r"/admin/api/function/add", AdminFunctionApiAddHandler),
        (r"/admin/api/function/update", AdminFunctionApiUpdateHandler),
        (r"/admin/api/function/delete", AdminFunctionApiDeleteHandler),
        (r"/admin/api/function/parents", AdminFunctionApiParentsHandler),

        # 智能瞭望
        (r"/admin/lookout-manage", LookoutManageHandler),
        (r"/admin/lookout-collect", LookoutCollectHandler),
        (r"/admin/api/lookout/source/list", LookoutSourceListHandler),
        (r"/admin/api/lookout/source/add", LookoutSourceAddHandler),
        (r"/admin/api/lookout/source/update", LookoutSourceUpdateHandler),
        (r"/admin/api/lookout/source/delete", LookoutSourceDeleteHandler),
        (r"/admin/api/lookout/collect/run", LookoutCollectRunHandler),
        (r"/admin/api/lookout/data/list", LookoutDataListHandler),
        (r"/admin/api/lookout/data/delete", LookoutDataDeleteHandler),

        # 模型管理
        (r"/admin/model", AdminModelHandler),
        (r"/admin/api/model/list", AdminModelListHandler),
        (r"/admin/api/model/add", AdminModelAddHandler),
        (r"/admin/api/model/update", AdminModelUpdateHandler),
        (r"/admin/api/model/delete", AdminModelDeleteHandler),
        (r"/admin/api/model/setdefault", AdminModelSetDefaultHandler),
        (r"/admin/api/model/chat", AdminModelChatHandler),
        (r"/admin/api/model/stats", AdminModelStatsHandler),

        # 数据管理
        (r"/admin/data-warehouse", DataWarehouseHandler),

        # 接口服务
        (r"/admin/api-manage", ApiManageHandler),
        (r"/admin/api/manage/list", ApiManageListHandler),
        (r"/admin/api/manage/add", ApiManageAddHandler),
        (r"/admin/api/manage/update", ApiManageUpdateHandler),
        (r"/admin/api/manage/delete", ApiManageDeleteHandler),
        (r"/admin/api/manage/categories", ApiManageCategoriesHandler),

        # 智能服务
        (r"/admin/digital-employee", DigitalEmployeeManageHandler),
        (r"/admin/api/digital-employee/list", DigitalEmployeeListHandler),
        (r"/admin/api/digital-employee/add", DigitalEmployeeAddHandler),
        (r"/admin/api/digital-employee/update", DigitalEmployeeUpdateHandler),
        (r"/admin/api/digital-employee/delete", DigitalEmployeeDeleteHandler),
        (r"/admin/api/digital-employee/all", DigitalEmployeeAllHandler),

        # 数智大屏
        (r"/admin/data-screen", DataScreenHandler),

        # 系统统计
        (r"/admin/system-stats", SystemStatsHandler),

        # 系统设置
        (r"/admin/system-config", SystemConfigHandler),
        (r"/admin/audit", AuditHandler),
    ], **settings)


if __name__ == "__main__":
    init_db()

    from app.models.user import UserRepository
    from app.models.db import get_connection
    from app.models.role import RoleRepository, UserRoleRepository
    import sqlite3

    admin_user = UserRepository.get_user_by_username("admin")
    if admin_user:
        admin_role = RoleRepository.get_by_name("超级管理员")
        if admin_role:
            conn = get_connection()
            existing = conn.execute(
                "SELECT COUNT(*) FROM user_roles WHERE user_id = ? AND role_id = ?",
                (admin_user["id"], admin_role["id"])
            ).fetchone()[0]
            conn.close()
            if existing == 0:
                UserRoleRepository.assign_roles(admin_user["id"], [admin_role["id"]])

    if UserRepository.verify_user("admin", "admin888"):
        print("管理员账号验证成功: admin / admin888", flush=True)
    else:
        UserRepository.delete_users([admin_user["id"]] if admin_user else [])
        if UserRepository.create_user("admin", "admin888"):
            print("管理员账号已重置: admin / admin888", flush=True)
        else:
            print("管理员账号重置失败，请检查数据库", flush=True)

    app = make_app()
    server = HTTPServer(app)

    server.bind(10086)

    # Windows 下不能用 start(0)，这里用 1
    server.start(1)

    print("====== Server Start ====== : 10086 ======", flush=True)

    tornado.ioloop.IOLoop.current().start()