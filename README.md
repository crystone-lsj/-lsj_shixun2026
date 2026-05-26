# AI 智能瞭望与智能问数系统

## 项目概述

本项目是一个基于 **Tornado** 框架构建的 **AI 智能瞭望与智能问数系统**。系统采用经典的 **MVC（Model-View-Controller）架构** 与 **B/S（Browser/Server）模式**。当前阶段已完成基础框架搭建及**用户登录/认证功能**的开发与验证，后续将基于此框架逐步实现智能问数、数据仓库、数字员工、瞭望管理等核心业务模块。

---

## 技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端核心 | Python | 3.12+ | 主编程语言 |
| Web 框架 | Tornado | 6.5.5 | 异步 Web 服务器 |
| 数据库 | SQLite3 | 内置 | 关系型数据库，预留 MySQL/PostgreSQL |
| 前端基础 | HTML5 + CSS3 + JavaScript | - | 原生前端技术 |
| 后台 UI | layui | 2.13.6 | 后台管理 UI 组件库（本地化） |
| 响应式 UI | Bootstrap | 5.3.8 | 响应式前端框架（本地化） |
| 图标库 | FontAwesome | 5.15.4 | 矢量图标集（本地化） |
| 模板引擎 | Tornado Template | 内置 | 服务端 HTML 模板 |
| 虚拟环境 | venv | Python 内置 | 依赖隔离 |

> **重要**: layui、Bootstrap、FontAwesome 均已本地化存放于 `app/static/dist/`，**禁止引用互联网 CDN 资源**。

---

## 架构设计

系统遵循 **MVC** 设计模式，各层职责明确：

### 1. 架构分层
- **Controller 层 (`app/controllers/`)**: 负责接收 HTTP 请求、处理业务逻辑调度、返回响应。
- **Model 层 (`app/models/`)**: 负责数据访问、数据库操作、业务实体封装。
- **View 层 (`app/templates/` + `app/static/`)**: 负责页面渲染与静态资源管理。

### 2. 核心机制
- **路由分发**: `app.py` 中通过 `tornado.web.Application` 统一配置 URL 路由映射。
- **会话管理**: 基于 Tornado `secure_cookie` 实现轻量级 Session 管理。
- **权限控制**: 通过 `BaseHandler` 统一拦截，结合 `@tornado.web.authenticated` 装饰器实现登录态校验。
- **安全防护**: 内置 XSRF 防护、密码哈希加盐存储、SQL 参数化查询防注入。

---

## 目录结构

```text
cnAgentOS/
│
├─ app.py                  # [主入口] 服务启动、路由配置、全局设置
├─ requirements.md         # [需求文档] 业务功能需求规划
├─ app.md                  # [结构说明] 目录结构描述文件
├─ test.py                 # [测试脚本] 单元测试与临时用例
├─ README.md               # [本文档] 项目说明与开发指南
│
├─ database/               # [数据库] SQLite 数据库文件
│  └─ app.db
│
├─ app/                    # [主应用包] MVC 业务代码
│  ├─ __init__.py          # 包初始化 (注意: 文件名可能为 _init_.py)
│  │
│  ├─ controllers/         # [控制层] 请求处理与路由逻辑
│  │  ├─ base.py           # 基础 Handler (登录态获取、公共逻辑)
│  │  ├─ auth.py           # 认证控制器 (登录/注册/退出)
│  │  └─ home.py           # 首页控制器
│  │
│  ├─ models/              # [模型层] 数据访问与实体
│  │  ├─ db.py             # 数据库连接、初始化建表
│  │  └─ user.py           # 用户数据仓库 (CRUD、密码验证)
│  │
│  ├─ templates/           # [视图层] HTML 模板
│  │  ├─ base.html         # 基础模板 (Layout)
│  │  ├─ login.html        # 登录页
│  │  ├─ index.html        # 后台首页
│  │  └─ register.html     # 注册页 (占位)
│  │
│  └─ static/              # [静态资源]
│     ├─ css/base.css      # 全局样式
│     ├─ js/base.js        # 全局脚本
│     └─ dist/             # [第三方组件本地化目录]
│        ├─ layui-2.13.6/  # layui UI 框架
│        ├─ bootstrap-5.3.8-dist/
│        │  └─ bootstrap-5.3.8-dist/
│        │     ├─ css/     # Bootstrap CSS
│        │     └─ js/      # Bootstrap JS
│        └─ fontawesome-free-5.15.4-web/
│           └─ fontawesome-free-5.15.4-web/
│              ├─ css/     # FontAwesome CSS
│              ├─ js/      # FontAwesome JS
│              └─ webfonts/ # 字体文件
│
└─ venv/                   # [虚拟环境] Python 依赖隔离环境
```

---

## 已实现功能

### 1. 用户认证系统
- **登录**: `/auth/login` (支持 GET 渲染 / POST 提交验证)
- **注销**: `/auth/logout` (清除 Cookie 并跳转)
- **会话保持**: 登录后通过 `secure_cookie` 维持登录态
- **注册**: 数据层已实现 `create_user`，视图层 `register.html` 已创建（待对接 Controller）

### 2. 安全机制
- **XSRF 防护**: 全局开启 `xsrf_cookies=True`，表单包含 `{% module xsrf_form_html() %}`
- **密码安全**: 使用 `PBKDF2-HMAC-SHA256` 算法，配合 `100,000` 次迭代与随机 Salt
- **SQL 防注入**: 全量使用参数化查询 `conn.execute("...", (params,))`
- **路由保护**: 敏感路由使用 `@tornado.web.authenticated` 装饰器自动重定向未登录用户

### 3. 数据库初始化
- 服务启动时自动检查并创建 `users` 表
- 表结构包含：`id`, `username`, `password_hash`, `salt`, `create_at`

---

## 路由映射表

### 前台路由
| URL 路径          | 请求方法 | 处理器                 | 说明                 | 权限要求   |
| ----------------- | -------- | ---------------------- | -------------------- | ---------- |
| `/`               | GET      | `IndexHandler`         | 前台首页             | **需登录** |
| `/auth/login`     | GET/POST | `LoginHandler`         | 前台登录             | 公开       |
| `/auth/logout`    | POST     | `LogoutHandler`        | 前台退出             | 公开       |

### 后台管理路由
| URL 路径                    | 请求方法 | 处理器                     | 说明                 | 权限要求   |
| --------------------------- | -------- | -------------------------- | -------------------- | ---------- |
| `/admin/login`              | GET/POST | `AdminLoginHandler`        | 后台管理员登录       | 公开       |
| `/admin/logout`             | GET      | `AdminLogoutHandler`       | 后台管理员退出       | **需登录** |
| `/admin`                    | GET      | `AdminIndexHandler`        | 后台管理首页（框架） | **需登录** |
| `/admin/user`               | GET      | `AdminUserHandler`         | 用户管理页面         | **需登录** |
| `/admin/api/user/list`      | GET      | `AdminUserListHandler`     | 用户列表 API（分页） | **需登录** |
| `/admin/api/user/add`       | POST     | `AdminUserAddHandler`      | 新增用户 API         | **需登录** |
| `/admin/api/user/update`    | POST     | `AdminUserUpdateHandler`   | 修改用户 API         | **需登录** |
| `/admin/api/user/delete`    | POST     | `AdminUserDeleteHandler`   | 删除用户 API         | **需登录** |

---

## 核心代码逻辑解析

### 1. Controller 继承链
```text
tornado.web.RequestHandler
    └── BaseHandler (app/controllers/base.py)
            ├── get_current_user() -> 从 secure_cookie 读取 username
            └── LoginHandler (app/controllers/auth.py)
            └── IndexHandler (app/controllers/home.py)
```
- `BaseHandler` 覆写了 `get_current_user`，这是 Tornado 认证体系的核心。当 `@authenticated` 触发时，框架会调用此方法，返回 `None` 则跳转至 `login_url`。

### 2. 数据库访问模式
- **连接管理**: `db.py` 提供 `get_connection()`，自动处理路径拼接与 `Row` 工厂设置（支持字典式访问字段）。
- **事务管理**: 使用 `with get_connection() as conn:` 上下文管理器，确保连接自动关闭。
- **建表逻辑**: `init_db()` 使用 `CREATE TABLE IF NOT EXISTS`，保证启动幂等性。

### 3. 密码验证流程
1. 用户提交 `username` + `password`
2. `UserRepository.get_user_by_username` 查询数据库获取 `salt` 和 `password_hash`
3. 使用相同的 Salt 和算法对提交的密码进行哈希计算
4. 比对计算结果与数据库存储的 Hash 值

---

## 开发指南 (Dev Guidelines)

### 1. 如何添加新的页面/功能

#### 步骤 1: 定义路由 (`app.py`)
```python
from app.controllers.my_module import MyHandler

# 在 make_app 中添加
(r"/my/path", MyHandler),
```

#### 步骤 2: 创建 Controller (`app/controllers/my_module.py`)
```python
import tornado.web
from app.controllers.base import BaseHandler

class MyHandler(BaseHandler):
    @tornado.web.authenticated  # 如果需要登录保护
    def get(self):
        self.render("my_page.html", title="我的页面")
```

#### 步骤 3: 创建 View (`app/templates/my_page.html`)
```html
{% extends "base.html" %}
{% block body %}
<h1>我的页面</h1>
{% end %}
```

#### 步骤 4: (可选) 创建 Model (`app/models/my_model.py`)
```python
from app.models.db import get_connection

class MyRepository:
    @staticmethod
    def get_data():
        with get_connection() as conn:
            return conn.execute("SELECT * FROM my_table").fetchall()
```

### 2. 编码规范
- **文件命名**: 使用小写+下划线，如 `user_profile.py`
- **类命名**: 驼峰命名，如 `UserRepository`, `LoginHandler`
- **缩进**: 统一使用 4 空格
- **注释**: 关键业务逻辑需添加中文注释
- **安全性**: 所有数据库操作必须参数化；所有表单必须包含 XSRF Token

### 3. 数据库扩展
- 当前使用 SQLite，若需切换 MySQL/PostgreSQL：
    - 修改 `db.py` 中的连接逻辑
    - 保持 `get_connection()` 接口不变，确保上层 Model 无感知
    - 建议引入 ORM (如 SQLAlchemy) 或保持现有轻量级封装

### 4. 测试方法
- 使用 `test.py` 编写临时用例
- 运行方式：在 `venv` 环境下执行 `python test.py`
- 示例：
    ```python
    from app.models.user import UserRepository
    print(UserRepository.verify_user("admin", "123456"))
    ```

---

## 环境配置与运行

### 1. 环境准备
```bash
# 进入虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖 (如有 requirements.txt)
pip install -r requirements.txt
```

### 2. 启动服务
```bash
python app.py
```
- 默认端口: `10086`
- 访问地址: `http://localhost:10086`
- 服务启动后会自动执行 `init_db()` 初始化数据库

### 3. 测试账号
- 通过 `test.py` 可初始化测试账号，如 `admin / 123456`

---

## 后续开发规划 (基于 requirements.md)

根据需求文档，系统后续需完成以下模块开发：

### 前端-用户侧
- [ ] 智能问数界面 (LLM 交互窗口)
- [ ] 数据展示容器 (文本/图表/向量检索结果)

### 后端-管理侧
- [ ] **用户管理**: 用户列表、角色分配、权限控制
- [ ] **数字员工**: 数据查询、天气、新闻、音乐、电影等 Agent 集成
- [ ] **模型引擎**: 动态模型切换、本地/远程模型接入、Token 统计、流式响应配置
- [ ] **瞭望管理**: 数据源管理、CSRF/SSRF 防护、批量采集
- [ ] **数据仓库**: 非关系型/关系型/向量数据库集成
- [ ] **深度采集**: 爬虫或 API 数据获取
- [ ] **数智大屏**: 3D WebGL 可视化、报表组件

---

## 注意事项

1. **文件命名规范**: 当前项目中 `app` 包的初始化文件名为 `_init_.py` (单下划线)，Python 标准应为 `__init__.py` (双下划线)。若后续导入出现问题，请检查此文件名。
2. **Cookie Secret**: `app.py` 中的 `cookie_secret` 目前为测试值，生产环境务必更换为高强度随机字符串。
3. **并发处理**: Tornado 为异步非阻塞框架，编写耗时操作（如大模型调用）时建议使用 `async/await` 避免阻塞 IOLoop。
4. **注册功能**: `register.html` 模板已存在但 Controller 尚未实现，开发注册功能时需注意密码强度校验与唯一性检查。
5. **静态资源**: 使用 `static_url()` 生成静态资源路径，便于后续接入 CDN 或添加版本戳。
6. **前端组件本地化**: layui、Bootstrap、FontAwesome 均已解压至 `app/static/dist/`，**所有前端开发必须使用本地资源，禁止引用互联网 CDN**。
7. **layui 压缩包问题**: `layui 2.13.6.zip` 解压后发现内容不是 layui 框架，而是其他文件（Superpowers Factory Bridge）。后续需要确认并获取正确的 layui 2.13.6 本地包。

---

## 关联文档

- **需求跟踪文档**: [requirements.md](file:///c:/Users/pc/Desktop/zhinengshixun20260515/day4/cnAgentOS/requirements.md) - 需求清单、状态跟踪、数据库规划、优先级建议
- **项目结构说明**: [app.md](file:///c:/Users/pc/Desktop/zhinengshixun20260515/day4/cnAgentOS/app.md) - 目录结构描述文件

---

> 本文档基于项目当前代码库生成，旨在指导后续开发工作。开发过程中请随时更新本文档以保持同步。
