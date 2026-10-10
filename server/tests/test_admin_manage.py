"""管理员管理模块：后台管理账号的建、改、停用、重置密码与越权防护。"""
from __future__ import annotations

from app.extensions import db
from app.models import OperationLog, User


def _body(resp) -> dict:
    return resp.get_json()


def test_create_manager_by_admin(client, login_as, admin):
    """管理员可新建楼管账号，默认启用且视为已身份核对。"""
    login_as(admin)
    resp = client.post("/api/v1/admin/admins", json={
        "username": "staff_new", "password": "Staff@2026", "role": "staff",
        "real_name": "王保卫", "college": "保卫处",
    })
    assert resp.status_code == 200
    user = User.query.filter_by(username="staff_new").first()
    assert user is not None and user.role == "staff" and user.status == "active"
    assert user.verified is True
    assert user.check_password("Staff@2026")


def test_create_manager_duplicate_username(client, login_as, admin, staff):
    """账号重名必须被拒绝，不产生脏数据。"""
    login_as(admin)
    resp = client.post("/api/v1/admin/admins", json={
        "username": staff.username, "password": "Staff@2026", "role": "staff",
    })
    assert resp.status_code == 400
    assert "已被占用" in _body(resp)["msg"]


def test_create_manager_weak_password(client, login_as, admin):
    """弱密码被强度策略拦截。"""
    login_as(admin)
    resp = client.post("/api/v1/admin/admins", json={
        "username": "weak_pwd_user", "password": "123", "role": "staff",
    })
    assert resp.status_code == 400
    assert User.query.filter_by(username="weak_pwd_user").first() is None


def test_create_manager_forbidden_for_student(client, login_as, student):
    """学生越权访问管理员管理接口 → 403。"""
    login_as(student)
    resp = client.get("/api/v1/admin/admins")
    assert resp.status_code == 403
    resp = client.post("/api/v1/admin/admins", json={
        "username": "hacker", "password": "Hack@2026", "role": "admin",
    })
    assert resp.status_code == 403


def test_create_manager_forbidden_for_staff(client, login_as, staff):
    """楼管可以看后台统计，但不能管理管理员账号。"""
    login_as(staff)
    resp = client.post("/api/v1/admin/admins", json={
        "username": "hacker2", "password": "Hack@2026", "role": "staff",
    })
    assert resp.status_code == 403


def test_admins_list_excludes_students(client, login_as, admin, student, staff):
    """列表中只出现管理侧账号，学生不应出现在管理员管理页。"""
    login_as(admin)
    resp = client.get("/api/v1/admin/admins")
    items = _body(resp)["data"]["items"]
    usernames = [i["username"] for i in items]
    assert student.username not in usernames
    assert staff.username in usernames and admin.username in usernames
    assert _body(resp)["data"]["staff_count"] >= 1


def test_reset_password_and_login(client, login_as, admin, staff):
    """重置密码后可用新密码登录，旧密码失效。"""
    login_as(admin)
    resp = client.post(f"/api/v1/admin/admins/{staff.id}/password",
                       json={"password": "NewStaff@2026"})
    assert resp.status_code == 200
    staff = db.session.get(User, staff.id)
    assert staff.check_password("NewStaff@2026")
    assert not staff.check_password("Staff@123")

    client.post("/api/v1/auth/logout")
    resp = client.post("/api/v1/auth/login",
                       json={"username": staff.username, "password": "NewStaff@2026"})
    assert resp.status_code == 200


def test_can_not_disable_self(client, login_as, admin):
    """不能停用自己的账号。"""
    login_as(admin)
    resp = client.post(f"/api/v1/admin/admins/{admin.id}/status", json={"status": "disabled"})
    assert resp.status_code == 400
    assert "自己" in _body(resp)["msg"]


def test_can_not_change_own_role(client, login_as, admin):
    """管理员不能在「用户管理」页把自己降级，避免后台失联。"""
    login_as(admin)
    resp = client.post(f"/api/v1/admin/users/{admin.id}/role", json={"role": "student"})
    assert resp.status_code == 400
    assert "自己" in _body(resp)["msg"]
    assert db.session.get(User, admin.id).role == "admin"


def test_last_admin_protected(app, admin):
    """防御性规则：仅剩一个启用管理员时不允许再降级/停用（并发或后续引入超级管理员的场景）。"""
    import pytest

    from app.services import auth_service
    from app.repositories import UserRepository

    second = User(username="admin2", role="admin", status="active", real_name="副管理员")
    second.set_password("Admin@12345")
    db.session.add(second)
    db.session.commit()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(UserRepository, "count_active_admins", staticmethod(lambda: 1))
        with pytest.raises(auth_service.AuthError) as exc:
            auth_service.update_manager(second, {"role": "staff"}, admin)
    assert "最后一个" in str(exc.value)
    assert db.session.get(User, second.id).role == "admin"


def test_disable_staff_then_enable(client, login_as, admin, staff):
    """停用楼管后其无法登录，重新启用后恢复。"""
    login_as(admin)
    assert client.post(f"/api/v1/admin/admins/{staff.id}/status",
                       json={"status": "disabled"}).status_code == 200
    client.post("/api/v1/auth/logout")
    resp = client.post("/api/v1/auth/login",
                       json={"username": staff.username, "password": "Staff@123"})
    assert resp.status_code == 400

    login_as(admin)
    client.post(f"/api/v1/admin/admins/{staff.id}/status", json={"status": "active"})
    client.post("/api/v1/auth/logout")
    resp = client.post("/api/v1/auth/login",
                       json={"username": staff.username, "password": "Staff@123"})
    assert resp.status_code == 200


def test_update_manager_role_and_profile(client, login_as, admin, staff):
    """可修改姓名并把楼管提升为管理员。"""
    login_as(admin)
    resp = client.put(f"/api/v1/admin/admins/{staff.id}",
                      json={"real_name": "周楼管", "role": "admin", "phone": "13800000000"})
    assert resp.status_code == 200
    staff = db.session.get(User, staff.id)
    assert staff.role == "admin" and staff.real_name == "周楼管"


def test_update_rejects_student_account(client, login_as, admin, student):
    """管理员管理接口不接受学生账号，避免绕过角色校验改权。"""
    login_as(admin)
    resp = client.put(f"/api/v1/admin/admins/{student.id}", json={"role": "admin"})
    assert resp.status_code == 400
    assert "不是管理人员" in _body(resp)["msg"]


def test_manager_operations_are_logged(client, login_as, admin, staff):
    """所有管理操作写入日志，满足可追溯要求。"""
    login_as(admin)
    client.post(f"/api/v1/admin/admins/{staff.id}/password", json={"password": "NewStaff@2026"})
    actions = {log.action for log in OperationLog.query.all()}
    assert "manager_reset_password" in actions
    assert OperationLog.query.filter_by(action="manager_reset_password",
                                        target_id=staff.id).first() is not None
