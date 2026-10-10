"""用户与权限管理：注册、登录（含防爆破锁定）、身份认证、改密、后台改角色。"""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models import LoginAttempt, User
from app.models.user import (
    ROLES,
    ROLE_ADMIN,
    ROLE_STAFF,
    ROLE_STUDENT,
    STATUS_ACTIVE,
    STATUS_DISABLED,
)

MANAGER_ROLES = (ROLE_STAFF, ROLE_ADMIN)
from app.repositories import LoginAttemptRepository, UserRepository
from app.schemas import BusinessError
from app.services import log_service
from app.utils import check_password_strength, client_ip


class AuthError(BusinessError):
    """认证业务异常。"""

    default_msg = "认证失败"


def register_user(data: dict) -> User:
    """注册：唯一性校验 + 密码强度 + 加盐哈希。

    :param data: 已校验过的字典，含 username/password/email/student_no/real_name/phone/college
    """
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip() or None
    student_no = (data.get("student_no") or "").strip() or None

    if not username:
        raise AuthError("用户名不能为空")
    if UserRepository.by_username(username):
        raise AuthError("用户名已被占用")
    if email and UserRepository.by_email(email):
        raise AuthError("邮箱已被注册")
    if student_no and UserRepository.by_student_no(student_no):
        raise AuthError("该学号已注册")

    ok, msg = check_password_strength(password)
    if not ok:
        raise AuthError(msg)

    user = User(
        username=username,
        student_no=student_no,
        real_name=(data.get("real_name") or "").strip() or None,
        email=email,
        phone=(data.get("phone") or "").strip() or None,
        college=(data.get("college") or "").strip() or None,
        role=ROLE_STUDENT,
        status=STATUS_ACTIVE,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    log_service.record("user_register", user, "user", user.id, {"username": user.username})
    return user


def authenticate(username: str, password: str, ip: str | None = None) -> User:
    """登录：失败计数 + 锁定时长，成功清零。"""
    ip = ip or client_ip()
    cfg = current_app.config

    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=cfg["LOGIN_LOCK_MINUTES"])
    fails = LoginAttemptRepository.recent_fails(username, since)
    if fails >= cfg["LOGIN_MAX_RETRY"]:
        db.session.add(LoginAttempt(
            username=username, ip=ip, success=False,
            locked_until=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=cfg["LOGIN_LOCK_MINUTES"]),
        ))
        db.session.commit()
        log_service.record("user_login_blocked", None, "user", None,
                           {"username": username, "ip": ip, "fails": fails}, result="fail")
        raise AuthError(f"连续登录失败 {fails} 次，账号已锁定 {cfg['LOGIN_LOCK_MINUTES']} 分钟")

    user = UserRepository.by_username(username)
    if user is None:
        _record_fail(username, ip)
        raise AuthError("用户名或密码错误")

    if user.status != STATUS_ACTIVE:
        log_service.record("user_login_disabled", user, "user", user.id, {"ip": ip}, result="fail")
        raise AuthError("账号已被禁用，请联系管理员")

    if not user.check_password(password):
        _record_fail(username, ip)
        raise AuthError("用户名或密码错误")

    LoginAttemptRepository.clear(username)
    user.touch_login(ip)
    db.session.commit()
    log_service.record("user_login", user, "user", user.id, {"ip": ip})
    return user


def _record_fail(username: str, ip: str) -> None:
    db.session.add(LoginAttempt(username=username, ip=ip, success=False))
    db.session.commit()
    log_service.record("user_login_fail", None, "user", None,
                       {"username": username, "ip": ip}, result="fail")


def change_password(user: User, old_password: str, new_password: str) -> User:
    if not user.check_password(old_password):
        raise AuthError("原密码不正确")
    ok, msg = check_password_strength(new_password)
    if not ok:
        raise AuthError(msg)
    if new_password == old_password:
        raise AuthError("新密码不能与原密码相同")
    user.set_password(new_password)   # 重新生成随机盐
    db.session.commit()
    log_service.record("user_change_password", user, "user", user.id, {})
    return user


def verify_identity(user: User, student_no: str, real_name: str) -> User:
    """校内身份认证：学号 + 姓名。

    生产环境应改为调用学校统一身份认证（CAS/OAuth）或导入的学籍名录，
    此处以规则校验代替，保持接口不变即可平滑替换。
    """
    if not student_no or len(student_no) < 6:
        raise AuthError("学号格式不正确")
    if not real_name or len(real_name.strip()) < 2:
        raise AuthError("请填写真实姓名")
    existing = UserRepository.by_student_no(student_no)
    if existing and existing.id != user.id:
        raise AuthError("该学号已被其他账号认证")

    user.student_no = student_no
    user.real_name = real_name.strip()
    user.verified = True
    db.session.commit()
    log_service.record("user_verify", user, "user", user.id, {"student_no": student_no})
    return user


def set_user_status(user: User, operator, status: str) -> User:
    if status not in (STATUS_ACTIVE, STATUS_DISABLED):
        raise AuthError("未知账号状态")
    if operator is not None and user.id == operator.id:
        raise AuthError("不能停用自己")
    old = user.status
    user.status = status
    db.session.commit()
    log_service.record("user_status_change", operator, "user", user.id,
                       {"from": old, "to": status, "username": user.username})
    return user


def set_user_role(user: User, operator, role: str) -> User:
    if role not in ROLES:
        raise AuthError("未知角色")
    if role != user.role:
        # 禁止自我改角色：否则管理员可在「用户管理」页把自己降为学生，导致后台彻底失联
        _assert_not_self(user, operator, "修改角色")
        _assert_not_last_admin(user, "降级")
    old = user.role
    user.role = role
    db.session.commit()
    log_service.record("user_role_change", operator, "user", user.id,
                       {"from": old, "to": role, "username": user.username})
    return user


# ---------------------------------------------------------------- 管理人员（后台账号）


def _assert_not_self(user: User, operator, action: str) -> None:
    if operator is not None and user.id == operator.id:
        raise AuthError(f"不能{action}自己的账号，请由其他管理员操作")


def _assert_not_last_admin(user: User, action: str) -> None:
    """保护规则：系统必须至少保留一个启用状态的系统管理员。

    否则所有管理入口都不可达，后台将彻底无法登录（决策记录见 CHANGELOG）。
    """
    if user.role != ROLE_ADMIN or user.status != STATUS_ACTIVE:
        return
    if UserRepository.count_active_admins() <= 1:
        raise AuthError(f"系统是最后一个启用状态的管理员，不能{action}")


def create_manager(data: dict, operator) -> User:
    """后台新建管理人员账号（楼管/保卫处 或 系统管理员）。

    :param data: username / password / role / real_name / phone / email / college
    """
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or ROLE_STAFF).strip()
    email = (data.get("email") or "").strip() or None
    phone = (data.get("phone") or "").strip() or None

    if role not in MANAGER_ROLES:
        raise AuthError("管理人员角色只能是「楼管/保卫处」或「系统管理员」")
    if not username:
        raise AuthError("登录账号不能为空")
    if UserRepository.by_username(username):
        raise AuthError("登录账号已被占用")
    if email and UserRepository.by_email(email):
        raise AuthError("邮箱已被占用")
    ok, msg = check_password_strength(password)
    if not ok:
        raise AuthError(msg)

    user = User(
        username=username,
        real_name=(data.get("real_name") or "").strip() or None,
        email=email,
        phone=phone,
        college=(data.get("college") or "").strip() or None,
        role=role,
        status=STATUS_ACTIVE,
        verified=True,          # 管理账号由后台创建，视为已完成身份核对
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    log_service.record("manager_create", operator, "user", user.id,
                       {"username": username, "role": role})
    return user


def update_manager(user: User, data: dict, operator) -> User:
    """编辑管理人员资料与角色。"""
    before = {"role": user.role, "status": user.status, "real_name": user.real_name}

    if "real_name" in data:
        user.real_name = (data.get("real_name") or "").strip() or None
    if "phone" in data:
        user.phone = (data.get("phone") or "").strip() or None
    if "college" in data:
        user.college = (data.get("college") or "").strip() or None
    if "email" in data:
        email = (data.get("email") or "").strip() or None
        if email and UserRepository.by_email(email) and UserRepository.by_email(email).id != user.id:
            raise AuthError("邮箱已被占用")
        user.email = email

    if "role" in data and data.get("role"):
        role = data["role"].strip()
        if role not in MANAGER_ROLES:
            raise AuthError("管理人员角色只能是「楼管/保卫处」或「系统管理员」")
        if role != user.role:
            _assert_not_self(user, operator, "修改角色")
            _assert_not_last_admin(user, "降级")
            user.role = role

    if "status" in data and data.get("status"):
        status = data["status"].strip()
        if status not in (STATUS_ACTIVE, STATUS_DISABLED):
            raise AuthError("未知账号状态")
        if status != user.status:
            _assert_not_self(user, operator, "停用")
            _assert_not_last_admin(user, "停用")
            user.status = status

    db.session.commit()
    log_service.record("manager_update", operator, "user", user.id,
                       {"username": user.username, "before": before,
                        "after": {"role": user.role, "status": user.status}})
    return user


def reset_password(user: User, new_password: str, operator) -> User:
    """管理员重置他人密码（无需原密码），强制走密码强度策略。"""
    ok, msg = check_password_strength(new_password)
    if not ok:
        raise AuthError(msg)
    user.set_password(new_password)
    db.session.commit()
    log_service.record("manager_reset_password", operator, "user", user.id,
                       {"username": user.username})
    return user


# ---------------- 找回密码（忘记密码） ----------------
RESET_TOKEN_TTL_MINUTES = 30


def request_password_reset(username: str, student_no: str, real_name: str) -> str:
    """找回密码：校验身份（用户名 + 学号 + 真实姓名），签发一次性重置令牌。

    生产环境应将令牌通过邮件/短信下发；演示环境直接返回令牌供前端走重置流程。
    """
    user = UserRepository.by_username((username or "").strip())
    if not user:
        raise AuthError("用户不存在")
    if ((user.student_no or "").strip() != (student_no or "").strip()
            or (user.real_name or "").strip() != (real_name or "").strip()):
        raise AuthError("身份校验失败，请核对学号与真实姓名")
    if user.status != STATUS_ACTIVE:
        raise AuthError("账号已被禁用，请联系管理员")
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
    db.session.commit()
    log_service.record("user_request_reset", user, "user", user.id, {})
    return token


def reset_password_by_token(token: str, new_password: str) -> User:
    """凭一次性令牌重置密码（无需原密码）。"""
    user = UserRepository.by_reset_token((token or "").strip())
    now = datetime.now(UTC).replace(tzinfo=None)
    if not user or not user.reset_token_expire or user.reset_token_expire < now:
        raise AuthError("重置链接无效或已过期，请重新发起找回")
    ok, msg = check_password_strength(new_password)
    if not ok:
        raise AuthError(msg)
    if user.check_password(new_password):
        raise AuthError("新密码不能与当前密码相同")
    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expire = None
    db.session.commit()
    log_service.record("user_reset_password", user, "user", user.id, {})
    return user
