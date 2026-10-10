"""扩展单例：集中创建，供 create_app() 装配，避免模块间循环导入。"""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.session_protection = "basic"
# 前后端分离：未登录时由 app/__init__.py 注册 JSON 401 处理器，而非重定向
login_manager.login_view = None
login_manager.login_message = "请先登录"
login_manager.login_message_category = "warning"
