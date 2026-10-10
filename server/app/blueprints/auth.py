"""用户与权限管理模块：注册、登录、登出、改密、校内身份认证。

挂载前缀：/api/v1/auth
"""
from __future__ import annotations

from flask import Blueprint
from flask_login import current_user, login_user, logout_user

from app.blueprints import payload, user_public
from app.decorators import login_required_json
from app.extensions import db
from app.schemas import fail, ok
from app.services import auth_service

bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    """注册：用户名/邮箱/学号唯一性 + 密码强度 + 加盐哈希，成功后自动登录。"""
    data = payload()
    if not (data.get("username") or "").strip():
        return fail("用户名不能为空")
    if not data.get("password"):
        return fail("密码不能为空")

    user = auth_service.register_user(data)      # 业务异常由全局处理器转 JSON
    login_user(user)
    return ok({"user": user_public(user, full=True)}, msg="注册成功")


@bp.post("/login")
def login():
    """登录：连续失败达阈值锁定；成功清零失败计数并记录 IP。"""
    data = payload()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return fail("请填写用户名和密码")

    user = auth_service.authenticate(username, password)
    login_user(user, remember=bool(data.get("remember")))
    return ok({"user": user_public(user, full=True)}, msg="登录成功")


@bp.post("/logout")
@login_required_json
def logout():
    logout_user()
    return ok(msg="已退出登录")


@bp.post("/change-password")
@login_required_json
def change_password():
    data = payload()
    old = data.get("old_password") or ""
    new = data.get("new_password") or ""
    if not old or not new:
        return fail("请填写原密码与新密码")
    auth_service.change_password(current_user, old, new)
    return ok(msg="密码已修改，请牢记新密码")


@bp.post("/forgot-password")
def forgot_password():
    """找回密码（第一步）：校验身份，签发一次性重置令牌。"""
    data = payload()
    token = auth_service.request_password_reset(
        data.get("username") or "", data.get("student_no") or "", data.get("real_name") or "")
    return ok({"reset_token": token, "expire_in_minutes": auth_service.RESET_TOKEN_TTL_MINUTES},
              msg="身份校验通过，请使用重置令牌设置新密码")


@bp.post("/reset-password")
def reset_password_route():
    """找回密码（第二步）：凭令牌设置新密码（无需原密码）。"""
    data = payload()
    token = data.get("reset_token") or ""
    new = data.get("new_password") or ""
    if not token or not new:
        return fail("请填写重置令牌与新密码")
    auth_service.reset_password_by_token(token, new)
    return ok(msg="密码已重置，请使用新密码登录")


@bp.post("/verify")
@login_required_json
def verify():
    """校内身份认证：学号 + 真实姓名（生产可替换为学校 CAS/学籍库对接）。"""
    data = payload()
    user = auth_service.verify_identity(current_user, data.get("student_no") or "", data.get("real_name") or "")
    return ok({"user": user_public(user, full=True)}, msg="身份认证成功")


@bp.put("/profile")
@login_required_json
def update_profile():
    """完善个人资料：姓名、学院、手机、邮箱。"""
    data = payload()
    user = current_user
    if "real_name" in data:
        user.real_name = (data.get("real_name") or "").strip() or None
    if "college" in data:
        user.college = (data.get("college") or "").strip() or None
    if "phone" in data:
        user.phone = (data.get("phone") or "").strip() or None
    if "email" in data:
        user.email = (data.get("email") or "").strip() or None
    db.session.commit()
    return ok({"user": user_public(user, full=True)}, msg="资料已更新")
