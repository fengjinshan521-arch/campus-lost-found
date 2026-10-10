"""黑盒测试用例：等价类划分 + 边界值分析。

覆盖三类核心输入：
1. 注册口令强度（长度边界 7/8、字符类、4 连重复）
2. 学生认证（学号 5/6 位边界、真实姓名 1/2 字边界）
3. 登录锁定（连续失败 5 次后第 6 次锁定）
4. 发布拾获物品必填字段（标题/地点/分类 等价类）

仅验证「可观测行为」，不依赖内部实现。
"""
from __future__ import annotations

import pytest

from app.services import auth_service, item_service
from app.schemas import BusinessError


# ---------------- 1. 注册口令强度 ----------------
class TestPasswordStrength:
    def test_pw_length_boundary_short(self, app):
        """边界值：长度 7（< 最小 8）应被拒绝。"""
        with pytest.raises(BusinessError):
            auth_service.register_user({
                "username": "u_pw7", "password": "Ab12345",
                "email": "pw7@example.com", "student_no": "20990001",
            })

    def test_pw_length_boundary_min(self, app):
        """边界值：长度 8 且满足两类字符应注册成功。"""
        u = auth_service.register_user({
            "username": "u_pw8", "password": "Ab123456",
            "email": "pw8@example.com", "student_no": "20990002",
        })
        assert u.id and u.check_password("Ab123456")

    def test_pw_single_class_rejected(self, app):
        """等价类：纯数字（仅一类字符）应被拒绝。"""
        with pytest.raises(BusinessError):
            auth_service.register_user({
                "username": "u_pwnum", "password": "12345678",
                "email": "pwnum@example.com", "student_no": "20990003",
            })

    def test_pw_four_repeat_rejected(self, app):
        """等价类：含 4 位以上连续重复字符应被拒绝。"""
        with pytest.raises(BusinessError):
            auth_service.register_user({
                "username": "u_pwrp", "password": "aaaa1234",
                "email": "pwrp@example.com", "student_no": "20990004",
            })

    def test_pw_valid(self, app):
        """有效等价类：满足全部规则的口令应注册成功。"""
        u = auth_service.register_user({
            "username": "u_pwok", "password": "Student@123",
            "email": "pwok@example.com", "student_no": "20990005",
        })
        assert u.check_password("Student@123")


# ---------------- 2. 学生认证边界 ----------------
class TestVerifyIdentity:
    def test_student_no_boundary_5(self, student):
        """边界值：学号 5 位（< 最小 6）应被拒绝。"""
        with pytest.raises(BusinessError):
            auth_service.verify_identity(student, "12345", "张三")

    def test_student_no_boundary_6(self, student):
        """边界值：学号 6 位应通过认证。"""
        u = auth_service.verify_identity(student, "209901", "张三")
        assert u.student_no == "209901"

    def test_real_name_boundary_1(self, student):
        """边界值：真实姓名 1 字（< 最小 2）应被拒绝。"""
        with pytest.raises(BusinessError):
            auth_service.verify_identity(student, "209902", "张")

    def test_real_name_boundary_2(self, student):
        """边界值：真实姓名 2 字应通过认证。"""
        u = auth_service.verify_identity(student, "209903", "李四")
        assert u.real_name == "李四"


# ---------------- 3. 登录锁定边界 ----------------
class TestLoginLock:
    def test_lock_after_five_fails(self, student):
        """边界值：连续 5 次错误仍可尝试（返回密码错误），第 6 次触发锁定。"""
        wrong = "WrongPass@1"
        # 第 1~5 次：应提示「用户名或密码错误」，不锁定
        for i in range(5):
            with pytest.raises(BusinessError) as exc:
                auth_service.authenticate(student.username, wrong)
            assert "锁定" not in str(exc.value)
        # 第 6 次：累计 5 次失败，触发锁定
        with pytest.raises(BusinessError) as exc:
            auth_service.authenticate(student.username, wrong)
        assert "锁定" in str(exc.value)


# ---------------- 4. 发布拾获物品必填字段 ----------------
class TestFoundItemRequired:
    def _base(self, category):
        return {
            "title": "捡到黑色 iPhone13",
            "category_id": category.id,
            "place": "图书馆三楼",
            "happen_time": "2026-09-30T10:00",
            "description": "黑色 iPhone13",
            "features": ["黑色", "iPhone13"],
        }

    def test_missing_title(self, app, category, staff):
        """等价类：标题为空应被拒绝。"""
        data = self._base(category)
        data["title"] = ""
        with pytest.raises(BusinessError):
            item_service.create_found_item(data, staff)

    def test_missing_place(self, app, category, staff):
        """等价类：拾获地点为空应被拒绝。"""
        data = self._base(category)
        data.pop("place")
        with pytest.raises(BusinessError):
            item_service.create_found_item(data, staff)

    def test_missing_category(self, app, category, staff):
        """等价类：未选择分类应被拒绝。"""
        data = self._base(category)
        data.pop("category_id")
        with pytest.raises(BusinessError):
            item_service.create_found_item(data, staff)

    def test_valid_found_item(self, app, category, staff):
        """有效等价类：字段齐全应创建成功。"""
        item = item_service.create_found_item(self._base(category), staff)
        assert item.id and item.title == "捡到黑色 iPhone13"
