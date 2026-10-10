"""表现层装饰器：登录校验、角色校验。返回 JSON 而非重定向。"""
from __future__ import annotations

from functools import wraps

from flask_login import current_user

from app.models.user import STATUS_ACTIVE
from app.schemas import CODE_FORBIDDEN, CODE_UNAUTHORIZED, fail


def login_required_json(func):
    """替代 Flask-Login 的 login_required：未登录返回 JSON 401。"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return fail("请先登录", code=CODE_UNAUTHORIZED, status=401)
        if getattr(current_user, "status", STATUS_ACTIVE) != STATUS_ACTIVE:
            return fail("账号已被禁用", code=CODE_FORBIDDEN, status=403)
        return func(*args, **kwargs)

    return wrapper


def role_required(*roles: str):
    """角色校验：未登录 401；角色不符 403。roles 为空表示仅要求登录。"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return fail("请先登录", code=CODE_UNAUTHORIZED, status=401)
            if getattr(current_user, "status", STATUS_ACTIVE) != STATUS_ACTIVE:
                return fail("账号已被禁用", code=CODE_FORBIDDEN, status=403)
            if roles and current_user.role not in roles:
                return fail("没有操作权限", code=CODE_FORBIDDEN, status=403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(func):
    return role_required("admin")(func)


def staff_required(func):
    return role_required("staff", "admin")(func)
