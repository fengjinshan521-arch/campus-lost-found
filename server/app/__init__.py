"""应用工厂：装配扩展、蓝图、CORS、错误处理、上传文件路由。"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, request, send_from_directory

from .config import get_config
from .extensions import csrf, db, login_manager, migrate
from .schemas import init_error_handlers


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    app.json.ensure_ascii = False          # 中文不被转义为 \uXXXX
    app.json.sort_keys = False

    _ensure_dirs(app)
    _init_logging(app)
    _init_extensions(app)
    _init_cors(app)
    _init_blueprints(app)
    _init_upload_route(app)
    init_error_handlers(app)
    return app


def _ensure_dirs(app: Flask) -> None:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "logs"), exist_ok=True)


def _init_logging(app: Flask) -> None:
    log_path = os.path.join(app.root_path, "..", "logs", "lostfound.log")
    handler = RotatingFileHandler(log_path, maxBytes=2 * 1024 * 1024,
                                  backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)


def _init_cors(app: Flask) -> None:
    """轻量 CORS：仅对白名单来源回写头部，支持携带 Cookie 会话。
    开发期前端走 Vite 代理（同源），此处作为直连调试的兜底。"""

    @app.after_request
    def _add_cors(resp):
        origin = request.headers.get("Origin")
        allow = app.config.get("CORS_ORIGINS") or []
        if origin and (origin in allow or "*" in allow):
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Headers"] = ", ".join(app.config["CORS_ALLOW_HEADERS"])
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            resp.headers["Access-Control-Expose-Headers"] = ", ".join(app.config["CORS_EXPOSE_HEADERS"])
        return resp

    @app.before_request
    def _handle_preflight():
        if request.method == "OPTIONS":
            from flask import make_response

            return make_response("", 204)


def _init_blueprints(app: Flask) -> None:
    from .blueprints.admin import bp as admin_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.claims import bp as claims_bp
    from .blueprints.items import bp as items_bp
    from .blueprints.main import bp as main_bp
    from .blueprints.notify import bp as notify_bp

    app.register_blueprint(main_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(items_bp, url_prefix="/api/v1/items")
    app.register_blueprint(claims_bp, url_prefix="/api/v1/claims")
    app.register_blueprint(notify_bp, url_prefix="/api/v1/notifications")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")


def _init_upload_route(app: Flask) -> None:
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
