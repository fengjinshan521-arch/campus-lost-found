"""pytest 公共夹具：测试库隔离、各角色用户、物品与登录助手。"""
from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pymysql
from sqlalchemy.engine.url import make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()
os.environ["FLASK_ENV"] = "testing"

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Category, User  # noqa: E402
from app.models.user import ROLE_ADMIN, ROLE_STAFF, ROLE_STUDENT  # noqa: E402

STUDENT_PWD = "Student@123"
STAFF_PWD = "Staff@123"
ADMIN_PWD = "Admin@12345"


def _ensure_test_database() -> None:
    """测试库不存在时自动创建（MySQL 不会自动建库）。"""
    from app.config import get_config

    url = make_url(get_config("testing").SQLALCHEMY_DATABASE_URI)
    conn = pymysql.connect(host=url.host or "127.0.0.1", port=url.port or 3306,
                           user=url.username, password=url.password or "", charset="utf8mb4")
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(scope="function")
def app():
    _ensure_test_database()
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def category(app) -> Category:
    cat = Category(name="电子设备", code="device", sort_order=1, is_active=True)
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture
def category_other(app) -> Category:
    cat = Category(name="衣物箱包", code="clothes", sort_order=2, is_active=True)
    db.session.add(cat)
    db.session.commit()
    return cat


def _make_user(username: str, role: str, password: str, **extra) -> User:
    user = User(username=username, role=role, status="active", **extra)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student(app) -> User:
    return _make_user("student1", ROLE_STUDENT, STUDENT_PWD,
                      real_name="张三", student_no="20220001", college="计算机学院")


@pytest.fixture
def student2(app) -> User:
    return _make_user("student2", ROLE_STUDENT, STUDENT_PWD,
                      real_name="李四", student_no="20220002", college="外国语学院")


@pytest.fixture
def staff(app) -> User:
    return _make_user("staff1", ROLE_STAFF, STAFF_PWD, real_name="楼管老周", college="后勤部")


@pytest.fixture
def admin(app) -> User:
    return _make_user("admin1", ROLE_ADMIN, ADMIN_PWD, real_name="管理员", college="信息化办公室")


def login(client, username: str, password: str):
    """登录助手：返回响应，便于断言错误场景。"""
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


@pytest.fixture
def login_as(client):
    """login_as(student) 直接完成登录。"""

    def _login(user: User):
        return login(client, user.username, {
            "student": STUDENT_PWD,
            "staff": STAFF_PWD,
            "admin": ADMIN_PWD,
        }.get(user.role, STUDENT_PWD))

    return _login


def found_payload(category, **override) -> dict:
    base = {
        "title": "捡到黑色 iPhone13 手机",
        "category_id": category.id,
        "place": "图书馆三楼自习室",
        "happen_time": datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1),
        "description": "黑色 iPhone13，透明壳，屏幕右下角有裂痕",
        "features": ["黑色", "iPhone13"],
        "storage_place": "保卫处 1 号柜",
    }
    base.update(override)
    return base


def lost_payload(category, **override) -> dict:
    base = {
        "title": "丢失黑色 iPhone13 手机",
        "category_id": category.id,
        "place": "图书馆二楼",
        "happen_time": datetime.now(UTC).replace(tzinfo=None) - timedelta(days=2),
        "description": "黑色 iPhone13，透明壳，屏幕有裂痕，内有照片",
        "features": ["黑色", "iPhone13"],
        "reward": "必有重谢",
    }
    base.update(override)
    return base


@pytest.fixture
def found_item(app, category, staff):
    from app.services import item_service

    return item_service.create_found_item(found_payload(category), staff)


@pytest.fixture
def lost_item(app, category, student):
    from app.services import item_service

    return item_service.create_lost_item(lost_payload(category), student)
