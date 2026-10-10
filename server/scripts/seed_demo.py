"""灌入演示数据：用于答辩演示与接口自测。

用法：
    python scripts/seed_demo.py               追加演示数据（已存在同名用户则跳过）
    python scripts/seed_demo.py --reset       清空业务数据后重新灌入
    python scripts/seed_demo.py --no-images   跳过自动配图（默认会为每条信息生成示意图）
"""
from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Category, Claim, FoundItem, LostItem, MatchRecord, Notification, OperationLog, User  # noqa: E402
from app.models.user import ROLE_STAFF, ROLE_STUDENT  # noqa: E402
from app.services import claim_service, item_service, match_service  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))     # 允许导入同目录图片脚本
try:
    from fetch_real_images import fetch_for_item             # noqa: E402  优先：网络真实照片
except Exception:
    fetch_for_item = None
try:
    from demo_images import HAS_PIL, ensure_item_image       # noqa: E402  回退：本地绘制示意图
except Exception:                                            # 脚本被移动等场景下不影响主流程
    HAS_PIL = False

    def ensure_item_image(item, entity_type, force=False):   # noqa: E702
        return None


def attach_image(item, entity_type: str) -> None:
    """配图：优先从 Pexels 抓真实照片，失败时回退本地绘制示意图。"""
    if fetch_for_item is not None:
        try:
            url, _ = fetch_for_item(item, entity_type)
            if url:
                return
        except Exception:
            pass
    if HAS_PIL:
        ensure_item_image(item, entity_type)

NOW = datetime.now(UTC).replace(tzinfo=None)

DEMO_USERS = [
    ("zhangsan", "张三", "2022010101", ROLE_STUDENT, "Student@123", "计算机学院"),
    ("lisi", "李四", "2022010102", ROLE_STUDENT, "Student@123", "外国语学院"),
    ("wangwu", "王五", "2022010103", ROLE_STUDENT, "Student@123", "机械学院"),
    ("staff01", "楼管老周", "S001", ROLE_STAFF, "Staff@123", "后勤保障部"),
]

# (标题, 分类名, 地点, 相对天数, 描述, 特征列表)
DEMO_FOUND = [
    ("捡到黑色 iPhone13 手机", "手机", "三教305教室", 2,
     "黑色 iPhone13，透明手机壳，屏幕右下角有裂痕，锁屏壁纸是小猫", ["黑色", "iPhone13", "透明壳"], False),
    ("捡到校园卡一张", "校园卡", "二食堂二楼", 1,
     "校园卡，卡面照片为男生，姓名部分已遮挡", ["校园卡", "蓝色卡套"], True),
    ("捡到蓝色保温杯", "水杯", "图书馆三楼自习室", 3,
     "蓝色保温杯，杯盖有磕碰痕迹，容量约 500ml", ["蓝色", "保温杯"], False),
    ("捡到一串钥匙", "宿舍钥匙", "1号楼宿舍楼下", 0,
     "三把钥匙，带一个蓝色小熊挂件", ["钥匙串", "蓝色挂件"], False),
    ("捡到黑色双肩包", "书包", "体育馆篮球场", 4,
     "黑色双肩包，内有高等数学教材一本", ["黑色", "双肩包"], False),
    ("捡到灰色围巾", "外套", "东门校车站", 5,
     "灰色羊毛围巾，边缘有流苏", ["灰色", "围巾"], False),
    ("捡到银色 U 盘", "电子设备", "行政楼教务处", 6,
     "银色金属 U 盘 32G，挂有红色绳", ["银色", "U盘"], False),
]

DEMO_LOST = [
    ("丢失黑色 iPhone13 手机", "手机", "图书馆二楼", 3,
     "黑色 iPhone13，透明壳，屏幕有裂痕，内有大量照片", ["黑色", "iPhone13", "透明壳"], "必有重谢"),
    ("丢失校园卡", "校园卡", "一食堂", 2,
     "校园卡丢失，姓名张三，学号 2022010101", ["校园卡", "蓝色卡套"], "谢谢好心人"),
    ("丢失蓝色保温杯", "水杯", "图书馆", 4,
     "蓝色保温杯，朋友送的，对我很重要", ["蓝色", "保温杯"], "酬金 50 元"),
    ("丢失钥匙串", "宿舍钥匙", "3号楼", 1,
     "宿舍钥匙串，带蓝色小熊挂件", ["钥匙串", "蓝色挂件"], ""),
    ("丢失黑色书包", "书包", "操场", 5,
     "黑色双肩包，里面有高数书和笔记本", ["黑色", "双肩包"], "重谢"),
]


def _cat_id(name: str) -> int | None:
    c = Category.query.filter_by(name=name).first()
    return c.id if c else None


def create_users() -> dict:
    users = {}
    for username, real_name, no, role, pwd, college in DEMO_USERS:
        u = User.query.filter_by(username=username).first()
        if u is None:
            u = User(username=username, real_name=real_name, student_no=no,
                     role=role, college=college, verified=True, status="active")
            u.set_password(pwd)
            db.session.add(u)
            db.session.flush()
        users[username] = u
    db.session.commit()
    return users


def create_found_items(users: dict, with_images: bool = True) -> list:
    items = []
    owners = ["staff01", "zhangsan", "lisi", "staff01", "wangwu", "staff01", "staff01"]
    for idx, (title, cat, place, days, desc, feats, sensitive) in enumerate(DEMO_FOUND):
        cid = _cat_id(cat)
        if cid is None:
            continue
        item = item_service.create_found_item(
            {
                "title": title,
                "category_id": cid,
                "place": place,
                "happen_time": NOW - timedelta(days=days),
                "description": desc,
                "features": feats,
                "storage_place": f"保卫处 {idx + 1} 号柜",
                "is_sensitive": sensitive,
            },
            users[owners[idx]],
        )
        if with_images:
            attach_image(item, "found_item")
        items.append(item)
    return items


def create_lost_items(users: dict, with_images: bool = True) -> list:
    items = []
    owners = ["zhangsan", "lisi", "wangwu", "zhangsan", "lisi"]
    for idx, (title, cat, place, days, desc, feats, reward) in enumerate(DEMO_LOST):
        cid = _cat_id(cat)
        if cid is None:
            continue
        item = item_service.create_lost_item(
            {
                "title": title,
                "category_id": cid,
                "place": place,
                "happen_time": NOW - timedelta(days=days),
                "description": desc,
                "features": feats,
                "reward": reward,
                "is_urgent": idx == 0,
            },
            users[owners[idx]],
        )
        if with_images:
            attach_image(item, "lost_item")
        items.append(item)
    return items


def create_demo_claim(found_items: list, users: dict):
    """制造一条待审核的认领单，便于演示审核流程。"""
    target = next((i for i in found_items if "保温杯" in i.title), None)
    if target is None or target.status != "unclaimed":
        return None
    try:
        return claim_service.submit_claim(
            target, users["wangwu"],
            {"reason": "蓝色保温杯，杯盖有磕碰，是我上周在图书馆丢的", "contact": "13800001111"},
        )
    except Exception as exc:          # 已存在申请等场景直接跳过
        print("      跳过演示认领单：", exc)
        return None


def reset_business_data() -> None:
    for model in (Notification, OperationLog, MatchRecord, Claim, FoundItem, LostItem):
        model.query.delete()
    # 物品被清空后其附件留痕即成孤儿，一并清理（认领凭证等其他类型保留）
    from app.models import Attachment
    Attachment.query.filter(Attachment.entity_type.in_(["found_item", "lost_item"])).delete(
        synchronize_session=False)
    db.session.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="先清空业务数据")
    parser.add_argument("--no-images", action="store_true", help="跳过自动配图")
    args = parser.parse_args()

    with_images = (not args.no_images) and HAS_PIL

    app = create_app()
    with app.app_context():
        if args.reset:
            print("[0/5] 清空业务数据 ...")
            reset_business_data()

        print("[1/5] 创建演示用户 ...")
        users = create_users()
        print(f"      用户 {len(users)} 位：{', '.join(users)}")

        print("[2/5] 创建拾获登记 ...")
        found = create_found_items(users, with_images=with_images)
        print(f"      拾获 {len(found)} 条")

        print("[3/5] 创建寻物启事 ...")
        lost = create_lost_items(users, with_images=with_images)
        print(f"      寻物 {len(lost)} 条")

        if with_images:
            print("      已为全部信息自动配图（Pexels 真实照片，失败回退本地示意图）")
        elif args.no_images:
            print("      已按参数跳过配图")

        print("[4/5] 创建演示认领单 ...")
        claim = create_demo_claim(found, users)
        print(f"      认领单：{claim.claim_no if claim else '（无）'}")

        print("[5/5] 全量匹配 ...")
        result = match_service.run_full_matching(push_notify=True)
        print(f"      新增匹配 {result['created']} 条，更新 {result['updated']} 条，通知 {result['notified']} 条")

    print("演示数据就绪 ✅")
    print("登录账号：admin/Admin@12345  staff01/Staff@123  zhangsan/Student@123")


if __name__ == "__main__":
    main()
