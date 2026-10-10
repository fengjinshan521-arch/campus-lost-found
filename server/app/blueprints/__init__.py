"""表现层（Blueprint 包）：共享的取参与序列化工具。

蓝图的职责边界（答辩要点）：
    解析参数 → 校验权限 → 调用 Service → 序列化结果
不含业务规则、不含裸 SQL；业务规则一律放在 app/services/，查询一律放在 app/repositories/。
"""
from __future__ import annotations

from flask import request
from flask_login import current_user

from app.utils import desensitize_email, desensitize_phone, desensitize_student_no


def payload() -> dict:
    """统一取参：优先 JSON（Axios 默认），其次 form（含文件上传的 multipart）。"""
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    if request.form:
        return request.form.to_dict()
    return {}


def _privileged(target_user) -> bool:
    """当前登录者是否为本人或职工/管理员。"""
    viewer = current_user
    if not getattr(viewer, "is_authenticated", False):
        return False
    return bool(getattr(viewer, "is_staff", False)) or getattr(viewer, "id", None) == getattr(target_user, "id", None)


def user_public(user, full: bool = False) -> dict | None:
    """用户信息序列化：手机/邮箱/学号默认脱敏，本人与职工可见原值。"""
    if user is None:
        return None
    seen = full or _privileged(user)
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "role": user.role,
        "role_label": user.role_label,
        "college": user.college,
        "verified": user.verified,
        "credit_score": user.credit_score,
        "student_no": user.student_no if seen else desensitize_student_no(user.student_no),
        "phone": user.phone if seen else desensitize_phone(user.phone),
        "email": user.email if seen else desensitize_email(user.email),
    }
