"""创建 / 提升系统管理员账号（运维入口，无需先登录后台）。

用法：
    python scripts/create_admin.py                         创建默认管理员 admin / Admin@12345
    python scripts/create_admin.py -u sysadmin -p Sys@2026 -n 张管理
    python scripts/create_admin.py -u staff02 -p Staff@123 -r staff -n 李四
    python scripts/create_admin.py --promote zhangsan -r admin   把已有账号提升为管理员
    python scripts/create_admin.py --list                   列出全部管理人员

说明：
    - 账号不存在时新建；已存在时按 --promote 决定是否改角色，并用 --password 重置密码。
    - 密码仍走 check_password_strength 强度策略，弱密码会直接拒绝。
    - 全过程写操作日志（manager_create / manager_update），与后台操作同样可追溯。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import User  # noqa: E402
from app.models.user import ROLE_ADMIN, ROLE_STAFF, STATUS_ACTIVE  # noqa: E402
from app.services import auth_service, log_service  # noqa: E402
from app.utils import check_password_strength  # noqa: E402


def list_managers() -> None:
    users = User.query.filter(User.role.in_([ROLE_STAFF, ROLE_ADMIN])) \
        .order_by(User.role.desc(), User.id).all()
    if not users:
        print("（暂无管理人员账号）")
        return
    print(f"{'ID':<5}{'账号':<16}{'姓名':<14}{'角色':<10}{'状态':<10}最后登录")
    for u in users:
        last = u.last_login_at.strftime("%Y-%m-%d %H:%M") if u.last_login_at else "-"
        print(f"{u.id:<5}{u.username:<16}{u.real_name or '-':<14}"
              f"{u.role_label:<10}{u.status:<10}{last}")


def main() -> int:
    parser = argparse.ArgumentParser(description="创建或提升系统管理员账号")
    parser.add_argument("-u", "--username", default="admin", help="登录账号（默认 admin）")
    parser.add_argument("-p", "--password", default="Admin@12345", help="登录密码（默认 Admin@12345）")
    parser.add_argument("-n", "--real-name", default="系统管理员", help="姓名")
    parser.add_argument("-r", "--role", default=ROLE_ADMIN, choices=[ROLE_ADMIN, ROLE_STAFF],
                        help="角色：admin 系统管理员 / staff 楼管（默认 admin）")
    parser.add_argument("--phone", default=None, help="手机号")
    parser.add_argument("--college", default=None, help="所属学院/部门")
    parser.add_argument("--promote", action="store_true",
                        help="账号已存在时允许改角色并重置密码（不加则直接退出）")
    parser.add_argument("--list", action="store_true", help="只列出当前管理人员，不做修改")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.list:
            list_managers()
            return 0

        ok, msg = check_password_strength(args.password)
        if not ok:
            print(f"[失败] 密码不符合强度策略：{msg}")
            return 1

        user = User.query.filter_by(username=args.username).first()
        if user is None:
            user = auth_service.create_manager({
                "username": args.username,
                "password": args.password,
                "role": args.role,
                "real_name": args.real_name,
                "phone": args.phone,
                "college": args.college,
            }, None)
            print(f"[完成] 已创建管理账号：{user.username} / {args.password}（{user.role_label}）")
        elif args.promote:
            before = (user.role, user.status)
            user.role = args.role
            user.status = STATUS_ACTIVE
            user.real_name = args.real_name or user.real_name
            if args.phone:
                user.phone = args.phone
            if args.college:
                user.college = args.college
            user.set_password(args.password)
            db.session.commit()
            log_service.record("manager_update", None, "user", user.id,
                               {"username": user.username, "before": {"role": before[0], "status": before[1]},
                                "after": {"role": user.role, "status": user.status}, "via": "cli"})
            print(f"[完成] 已更新管理账号：{user.username} / {args.password}（{user.role_label}）")
        else:
            print(f"[跳过] 账号 {args.username} 已存在（当前角色 {user.role_label}）。"
                  f"如需改角色或重置密码，请加 --promote")
            return 0

        list_managers()
        if args.password in ("Admin@12345", "Staff@123"):
            print("[提示] 使用的是默认密码，部署到生产环境前务必修改。")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
