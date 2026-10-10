"""端到端冒烟测试：不启动服务器，直接用 Flask 测试客户端跑通完整业务闭环。

    python scripts/smoke_test.py

覆盖链路：
    注册 → 登录 → 拾获登记 → 寻物发布 → 检索 → 匹配推荐 → 提交认领 → 审核通过 → 归档
    → 通知 → 统计 → 日志追溯
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import create_app  # noqa: E402

APP = create_app()
APP.config["WTF_CSRF_ENABLED"] = False      # 冒烟测试关闭 CSRF，专注业务流程
CLIENT = APP.test_client()

STEPS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    STEPS.append((name, ok, extra))
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {name} {extra}")


def body(resp) -> dict:
    return resp.get_json() or {}


def api(method: str, path: str, **kw) -> dict:
    resp = CLIENT.open(path, method=method, **kw)
    return body(resp)


def main() -> int:
    with APP.app_context():
        stamp = datetime.now(UTC).replace(tzinfo=None).strftime("%H%M%S")
        user_a = f"smoke_a{stamp}"
        user_b = f"smoke_b{stamp}"

        # 1. 注册两个用户
        r = api("POST", "/api/v1/auth/register", json={
            "username": user_a, "password": "Smoke@12345", "real_name": "冒烟甲",
            "student_no": f"9900{stamp}", "college": "测试学院",
        })
        check("注册用户A", r.get("code") == 0, r.get("msg", ""))

        r = api("POST", "/api/v1/auth/register", json={
            "username": user_b, "password": "Smoke@12345", "real_name": "冒烟乙",
        })
        check("注册用户B", r.get("code") == 0, r.get("msg", ""))

        # 2. 登录校验（错误密码应失败）
        r = api("POST", "/api/v1/auth/login", json={"username": user_a, "password": "wrong-pass"})
        check("错误密码登录被拒", r.get("code") != 0, r.get("msg", ""))

        # 3. 取字典，拿分类
        r = api("GET", "/api/v1/meta")
        cats = r.get("data", {}).get("categories", [])
        check("获取分类字典", len(cats) > 0, f"{len(cats)} 个一级分类")
        cat_id = cats[0]["id"]

        # 4. B 登记拾获
        found_time = (datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
        r = api("POST", "/api/v1/items/found", json={
            "title": f"冒烟测试捡到黑色水杯{stamp}", "category_id": cat_id,
            "place": "图书馆三楼自习室", "happen_time": found_time,
            "description": "黑色保温杯，杯盖有磕碰，500ml", "features": ["黑色", "保温杯"],
            "storage_place": "保卫处测试柜",
        })
        check("拾获登记", r.get("code") == 0, r.get("msg", ""))
        found_id = (r.get("data") or {}).get("id")

        # 5. A 发布寻物
        lost_time = (datetime.now(UTC).replace(tzinfo=None) - timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
        r = api("POST", "/api/v1/items/lost", json={
            "title": f"冒烟测试丢失黑色保温杯{stamp}", "category_id": cat_id,
            "place": "图书馆自习室", "happen_time": lost_time,
            "description": "黑色保温杯，杯盖磕碰过，对我很重要", "features": ["黑色", "保温杯"],
            "reward": "酬金 20 元",
        })
        check("寻物发布", r.get("code") == 0, r.get("msg", ""))
        lost_id = (r.get("data") or {}).get("id")

        # 6. 检索
        r = api("GET", f"/api/v1/items/found?kw={stamp}")
        check("模糊搜索命中", r.get("data", {}).get("total", 0) >= 1,
              f"total={r.get('data', {}).get('total')}")

        # 7. 匹配推荐
        r = api("GET", f"/api/v1/items/lost/{lost_id}/matches")
        matches = r.get("data", {}).get("matches", [])
        check("匹配推荐有结果", len(matches) >= 1,
              f"最高分 {matches[0]['score'] if matches else '-'}")

        # 8. 切换到 A 提交认领（B 是登记人）
        api("POST", "/api/v1/auth/logout")
        api("POST", "/api/v1/auth/login", json={"username": user_a, "password": "Smoke@12345"})
        r = api("POST", "/api/v1/claims/create", json={
            "found_item_id": found_id, "lost_item_id": lost_id,
            "reason": "黑色保温杯，杯盖有磕碰，是我前天在图书馆丢的", "contact": "13800002222",
        })
        check("提交认领", r.get("code") == 0, r.get("msg", ""))
        claim_id = (r.get("data") or {}).get("id")

        # 9. 重复提交应被拒
        r = api("POST", "/api/v1/claims/create", json={
            "found_item_id": found_id, "reason": "再提交一次试试看会不会被拒绝",
        })
        check("重复认领被拒", r.get("code") != 0, r.get("msg", ""))

        # 10. 切换到 B（登记人）审核通过
        api("POST", "/api/v1/auth/logout")
        api("POST", "/api/v1/auth/login", json={"username": user_b, "password": "Smoke@12345"})
        r = api("POST", f"/api/v1/claims/{claim_id}/approve", json={"comment": "特征描述吻合，予以通过"})
        check("审核通过", r.get("code") == 0, r.get("msg", ""))

        r = api("GET", f"/api/v1/items/found/{found_id}")
        check("物品状态变为已认领", (r.get("data", {}).get("item") or {}).get("status") == "claimed",
              (r.get("data", {}).get("item") or {}).get("status_label", ""))

        # 11. 归档
        r = api("POST", f"/api/v1/claims/{claim_id}/archive")
        check("归档结案", r.get("code") == 0, r.get("msg", ""))

        # 12. 归档后再次流转应被状态机拦截
        r = api("POST", f"/api/v1/claims/{claim_id}/reject", json={"comment": "归档后再驳回应当失败"})
        check("归档后非法流转被拦截", r.get("code") != 0, r.get("msg", "")[:40])

        # 13. 通知
        api("POST", "/api/v1/auth/logout")
        api("POST", "/api/v1/auth/login", json={"username": user_a, "password": "Smoke@12345"})
        r = api("GET", "/api/v1/notifications/")
        check("通知列表可读", r.get("code") == 0,
              f"未读 {r.get('data', {}).get('unread_count')} 条")

        # 14. 管理员统计与日志追溯
        api("POST", "/api/v1/auth/logout")
        api("POST", "/api/v1/auth/login", json={"username": "admin", "password": "Admin@12345"})
        r = api("GET", "/api/v1/admin/stats")
        check("管理员统计", r.get("code") == 0,
              f"认领率 {(r.get('data', {}) or {}).get('claim_rate', {}).get('rate_percent')}")

        r = api("GET", f"/api/v1/admin/logs/trace?target_type=claim&target_id={claim_id}")
        timeline = r.get("data", {}).get("timeline", [])
        actions = [t["action"] for t in timeline]
        check("认领单全链路可追溯", len(actions) >= 3, " → ".join(actions))

        # 15. 越权访问后台
        api("POST", "/api/v1/auth/logout")
        api("POST", "/api/v1/auth/login", json={"username": user_a, "password": "Smoke@12345"})
        r = api("GET", "/api/v1/admin/users")
        check("学生访问后台被拒", r.get("code") == 403, r.get("msg", ""))

    passed = sum(1 for _, ok, _ in STEPS if ok)
    total = len(STEPS)
    print("-" * 60)
    print(f"冒烟测试结果：{passed}/{total} 通过")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
