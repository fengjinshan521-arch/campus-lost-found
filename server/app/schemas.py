"""统一 JSON 响应封装与全局错误处理。

前后端分离约定：所有接口返回 {code, msg, data}，HTTP 状态码仅表达大类结果。
"""
from __future__ import annotations

import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from flask_wtf.csrf import CSRFError

from app.services.state_machine import InvalidTransition

# code 约定：0 成功；1 通用业务失败；401 未登录；403 无权限；10 状态流转非法
CODE_OK = 0
CODE_FAIL = 1
CODE_UNAUTHORIZED = 401
CODE_FORBIDDEN = 403
CODE_INVALID_TRANSITION = 10


class BusinessError(Exception):
    """业务异常：由 Service 抛出，表现层自动转为 JSON。"""

    status = 400
    code = CODE_FAIL
    default_msg = "业务处理失败"

    def __init__(self, msg: str | None = None, code: int | None = None, status: int | None = None):
        self.msg = msg or self.default_msg
        if code is not None:
            self.code = code
        if status is not None:
            self.status = status
        super().__init__(self.msg)

    def to_dict(self) -> dict:
        return {"code": self.code, "msg": self.msg, "data": None}


def ok(data=None, msg: str = "success"):
    return jsonify({"code": CODE_OK, "msg": msg, "data": data})


def fail(msg: str, code: int = CODE_FAIL, status: int = 400, data=None):
    return jsonify({"code": code, "msg": msg, "data": data}), status


def paginated(page_obj, items: list, extra: dict | None = None) -> dict:
    """把 Flask-SQLAlchemy 分页对象转为前端需要的结构。"""
    data = {
        "items": items,
        "total": page_obj.total,
        "page": page_obj.page,
        "pages": page_obj.pages,
        "per_page": page_obj.per_page,
        "has_prev": page_obj.has_prev,
        "has_next": page_obj.has_next,
    }
    if extra:
        data.update(extra)
    return data


def init_error_handlers(app: Flask) -> None:
    """注册全局异常处理器，保证任何异常都返回 JSON 而不是 HTML 错误页。"""

    @app.errorhandler(BusinessError)
    def _business(e: BusinessError):
        return jsonify(e.to_dict()), e.status

    @app.errorhandler(InvalidTransition)
    def _transition(e: InvalidTransition):
        return jsonify({"code": CODE_INVALID_TRANSITION, "msg": str(e), "data": None}), 400

    @app.errorhandler(CSRFError)
    def _csrf(e: CSRFError):
        return jsonify({"code": CODE_FORBIDDEN, "msg": "CSRF 校验失败，请刷新页面重试", "data": None}), 400

    @app.errorhandler(HTTPException)
    def _http(e: HTTPException):
        return jsonify({"code": e.code or 500, "msg": e.description or "请求异常", "data": None}), e.code or 500

    @app.errorhandler(Exception)
    def _server(e: Exception):
        logging.exception("未捕获异常 path=%s", getattr(request, "path", "-"))
        msg = "服务器内部错误" if not app.debug else f"{type(e).__name__}: {e}"
        return jsonify({"code": 500, "msg": msg, "data": None}), 500
