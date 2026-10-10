"""导出初始化 SQL：把库里的分类、管理员、系统参数固化为 sql/init_data.sql。

用法：python scripts/export_init_sql.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from app.config import get_config  # noqa: E402

Q = "'"


def esc(value) -> str:
    if value is None or value == "":
        return "NULL"
    return Q + str(value).replace(Q, "") + Q


def main() -> None:
    url = make_url(get_config().SQLALCHEMY_DATABASE_URI)
    conn = pymysql.connect(host=url.host, port=url.port or 3306, user=url.username,
                           password=url.password or "", database=url.database, charset="utf8mb4")
    cur = conn.cursor()

    lines = [
        "-- =============================================================",
        "-- 校园失物招领信息平台  初始化数据",
        "-- 执行顺序：先执行 sql/schema.sql，再执行本文件",
        "-- 说明：由 scripts/export_init_sql.py 从运行中数据库导出，与 ORM 模型一致",
        "-- =============================================================",
        "USE campus_lostfound;",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "",
        "-- 1. 物品分类：7 个一级分类 + 二级分类（自引用 parent_id）",
    ]

    cur.execute("SELECT id, name, code, parent_id, sort_order, is_active, description "
                "FROM t_category ORDER BY id")
    for cid, name, code, pid, sort_order, active, desc in cur.fetchall():
        lines.append(
            f"INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, "
            f"description, created_at, updated_at) VALUES "
            f"({cid}, {esc(name)}, {esc(code)}, {pid if pid is not None else 'NULL'}, "
            f"{sort_order}, {int(bool(active))}, {esc(desc)}, NOW(), NOW()) "
            f"ON DUPLICATE KEY UPDATE name = VALUES(name);"
        )

    lines += ["", "-- 2. 管理员账号：admin / Admin@12345（PBKDF2-HMAC-SHA256 + 随机盐）"]
    cur.execute("SELECT username, student_no, real_name, password_hash, salt, role, status, "
                "college, verified FROM t_user WHERE username = 'admin'")
    row = cur.fetchone()
    if row:
        username, sno, real, phash, salt, role, status, college, verified = row
        lines.append(
            f"INSERT INTO t_user (username, student_no, real_name, password_hash, salt, role, "
            f"status, college, verified, credit_score, created_at, updated_at) VALUES "
            f"({esc(username)}, {esc(sno)}, {esc(real)}, {esc(phash)}, {esc(salt)}, {esc(role)}, "
            f"{esc(status)}, {esc(college)}, {int(bool(verified))}, 100, NOW(), NOW()) "
            f"ON DUPLICATE KEY UPDATE username = username;"
        )

    lines += ["", "-- 3. 系统参数：匹配推荐六因子权重"]
    cur.execute("SELECT `key`, value, remark FROM t_system_setting")
    for key, value, remark in cur.fetchall():
        lines.append(
            f"INSERT INTO t_system_setting (`key`, value, remark, created_at, updated_at) VALUES "
            f"({esc(key)}, {esc(value)}, {esc(remark)}, NOW(), NOW()) "
            f"ON DUPLICATE KEY UPDATE value = VALUES(value);"
        )

    lines += ["", "SET FOREIGN_KEY_CHECKS = 1;", ""]
    out = Path(__file__).resolve().parents[1] / "sql" / "init_data.sql"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"已导出 {len(lines)} 行 → {out}")


if __name__ == "__main__":
    main()
