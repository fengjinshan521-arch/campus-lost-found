"""找回密码（忘记密码）流程用例。"""
from __future__ import annotations

import pytest

from app.services import auth_service
from app.schemas import BusinessError


def test_forgot_password_wrong_identity(student):
    """身份校验失败（学号/姓名不符）应被拒绝。"""
    with pytest.raises(BusinessError):
        auth_service.request_password_reset(student.username, "000000", student.real_name)
    with pytest.raises(BusinessError):
        auth_service.request_password_reset(student.username, student.student_no, "王五")


def test_forgot_password_and_reset(student):
    """正常流程：校验身份→拿到令牌→重置→新密码可登录、旧密码失效。"""
    token = auth_service.request_password_reset(student.username, student.student_no, student.real_name)
    assert token
    # 令牌立即可用
    auth_service.reset_password_by_token(token, "NewPass@123")
    # 新密码可登录
    u = auth_service.authenticate(student.username, "NewPass@123")
    assert u.id == student.id
    # 旧密码失效
    with pytest.raises(BusinessError):
        auth_service.authenticate(student.username, "Student@123")
    # 同令牌不可重复使用
    with pytest.raises(BusinessError):
        auth_service.reset_password_by_token(token, "Another@123")


def test_reset_with_invalid_token(student):
    """非法/错误令牌应被拒绝。"""
    with pytest.raises(BusinessError):
        auth_service.reset_password_by_token("not-a-real-token", "NewPass@123")
