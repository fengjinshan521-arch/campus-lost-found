"""建库建表 + 初始化基础数据。

用法：
    python scripts/init_db.py              建表并初始化（已存在则跳过）
    python scripts/init_db.py --drop       先删库再重建（危险，仅开发用）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 保证可导入 app 包

import pymysql  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from sqlalchemy.engine.url import make_url  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Category, SystemSetting, User  # noqa: E402
from app.models.user import ROLE_ADMIN  # noqa: E402

DEFAULT_CATEGORIES = [
    ("证件卡包", "card", ["身份证", "学生证", "银行卡", "校园卡"]),
    ("电子设备", "device", ["手机", "笔记本", "平板", "耳机", "充电宝"]),
    ("书籍文具", "book", ["教材", "笔记", "文具", "书包"]),
    ("衣物箱包", "clothes", ["外套", "围巾", "雨伞", "行李箱"]),
    ("钥匙", "key", ["宿舍钥匙", "车钥匙", "钥匙串"]),
    ("生活用品", "daily", ["水杯", "眼镜", "饰品", "运动器材"]),
    ("其他", "other", []),
]


def create_database_if_missing(uri: str) -> str:
    """MySQL 不会自动建库，先用裸连接把库建出来。"""
    url = make_url(uri)
    db_name = url.database
    print(f"[1/4] 检查数据库 {db_name} ...")
    conn = pymysql.connect(host=url.host or "127.0.0.1", port=url.port or 3306,
                           user=url.username, password=url.password or "", charset="utf8mb4")
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        print(f"      数据库 {db_name} 就绪")
    finally:
        conn.close()
    return db_name


def drop_database(uri: str) -> None:
    url = make_url(uri)
    conn = pymysql.connect(host=url.host or "127.0.0.1", port=url.port or 3306,
                           user=url.username, password=url.password or "", charset="utf8mb4")
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{url.database}`")
        conn.commit()
        print(f"      已删除数据库 {url.database}")
    finally:
        conn.close()


def init_categories() -> int:
    created = 0
    for order, (name, code, children) in enumerate(DEFAULT_CATEGORIES, start=1):
        parent = Category.query.filter_by(name=name).first()
        if parent is None:
            parent = Category(name=name, code=code, sort_order=order, is_active=True,
                              description=f"{name}类物品")
            db.session.add(parent)
            db.session.flush()
            created += 1
        for child in children:
            if Category.query.filter_by(name=child).first() is None:
                db.session.add(Category(name=child, parent_id=parent.id,
                                        sort_order=0, is_active=True))
                created += 1
    db.session.commit()
    return created


def init_admin() -> None:
    if User.query.filter_by(username="admin").first():
        print("      admin 已存在，跳过")
        return
    admin = User(username="admin", real_name="系统管理员", role=ROLE_ADMIN,
                 status="active", verified=True, college="信息化办公室")
    admin.set_password("Admin@12345")
    db.session.add(admin)
    db.session.commit()
    print("      已创建管理员：admin / Admin@12345（请首次登录后修改）")


def init_settings() -> None:
    import json

    if SystemSetting.query.filter_by(key="match_weights").first():
        return
    db.session.add(SystemSetting(
        key="match_weights",
        value=json.dumps({
            "category": 0.25, "keyword": 0.20, "location": 0.15,
            "time": 0.15, "feature": 0.15, "text": 0.10,
        }, ensure_ascii=False),
        remark="匹配推荐算法六因子权重",
    ))
    db.session.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drop", action="store_true", help="先删除数据库再重建")
    args = parser.parse_args()

    app = create_app()
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    print(f"[0/4] 连接串：{uri.split('@')[-1]}")

    if args.drop:
        drop_database(uri)
    create_database_if_missing(uri)

    with app.app_context():
        print("[2/4] 建表 ...")
        db.create_all()
        tables = [t.name for t in db.metadata.sorted_tables]
        print(f"      共 {len(tables)} 张表：{', '.join(tables)}")

        print("[3/4] 初始化分类 ...")
        n = init_categories()
        print(f"      新增分类 {n} 条")

        print("[4/4] 初始化管理员与系统参数 ...")
        init_admin()
        init_settings()

    print("完成 ✅")


if __name__ == "__main__":
    main()
