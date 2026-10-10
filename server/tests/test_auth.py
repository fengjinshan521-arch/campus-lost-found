"""用户与权限管理模块用例（8 条）。"""
from __future__ import annotations

from app.extensions import db
from app.models import User
from app.models.user import ROLE_STAFF, ROLE_STUDENT, STATUS_DISABLED
from app.services import auth_service
from app.schemas import BusinessError
from app.repositories import LoginAttemptRepository
from conftest import STUDENT_PWD, login
import pytest


def test_register_success(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "newbie", "password": "Newbie@123", "real_name": "新生",
        "student_no": "20220999",
    })
    assert resp.get_json()["code"] == 0
    assert User.query.filter_by(username="newbie").first() is not None


def test_register_duplicate_username_fails(client, student):
    resp = client.post("/api/v1/auth/register", json={
        "username": student.username, "password": "Another@123",
    })
    assert resp.get_json()["code"] != 0


def test_register_weak_password_rejected(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "weakpwd", "password": "123",
    })
    assert resp.get_json()["code"] != 0


def test_password_hashed_with_unique_salt():
    u1 = User(username="s1")
    u2 = User(username="s2")
    u1.set_password("Same@1234")
    u2.set_password("Same@1234")
    assert u1.password_hash != "Same@1234"          # 不存明文
    assert u1.salt != u2.salt                        # 同密码不同盐
    assert u1.password_hash != u2.password_hash      # 同密码不同哈希
    assert u1.check_password("Same@1234")
    assert not u1.check_password("Wrong@1234")


def test_login_success_and_wrong_password(client, student):
    ok_resp = login(client, student.username, STUDENT_PWD)
    assert ok_resp.get_json()["code"] == 0
    assert ok_resp.get_json()["data"]["user"]["username"] == student.username

    bad = login(client, student.username, "wrong-password")
    assert bad.get_json()["code"] != 0


def test_login_locked_after_max_retry(app, student):
    for _ in range(app.config["LOGIN_MAX_RETRY"]):
        try:
            auth_service.authenticate(student.username, "bad-password")
        except BusinessError:
            pass
    with pytest.raises(BusinessError) as exc:
        auth_service.authenticate(student.username, STUDENT_PWD)
    assert "锁定" in str(exc.value)


def test_disabled_user_cannot_login(app, student):
    student.status = STATUS_DISABLED
    db.session.commit()
    with pytest.raises(BusinessError) as exc:
        auth_service.authenticate(student.username, STUDENT_PWD)
    assert "禁用" in str(exc.value)


def test_student_cannot_access_admin_api(client, login_as, student):
    login_as(student)
    resp = client.get("/api/v1/admin/users")
    assert resp.status_code == 403
