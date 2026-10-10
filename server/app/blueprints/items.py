"""失物登记 / 拾获登记 / 分类检索与模糊搜索 / 匹配推荐。

挂载前缀：/api/v1/items
"""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, request
from flask_login import current_user

from app.blueprints import payload, user_public
from app.decorators import login_required_json
from app.extensions import db
from app.models import User
from app.repositories import FoundItemRepository, LostItemRepository
from app.schemas import fail, ok, paginated
from app.services import claim_service, item_service, match_service

bp = Blueprint("items", __name__)


# ---------------------------------------------------------------- 序列化


def _found_card(item, detail: bool = False) -> dict:
    data = item.to_dict()
    data["category_name"] = item.category.name if item.category else None
    data["founder"] = user_public(item.founder)
    if item.is_sensitive and not item_service.can_view_sensitive(item, current_user):
        data["description"] = "该物品为证件/卡包类敏感物品，完整信息需认领核实后查看"
        data["image_list"] = []
    if detail and item.claimed_by:
        data["claimed_by_user"] = user_public(db.session.get(User, item.claimed_by))
    return data


def _lost_card(item) -> dict:
    data = item.to_dict()
    data["category_name"] = item.category.name if item.category else None
    data["owner"] = user_public(item.owner)
    return data


def _search_args() -> dict:
    """把查询参数收敛成 Repository 的检索条件。"""

    def _date(key: str):
        raw = (request.args.get(key) or "").strip()
        if not raw:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    return {
        "keyword": (request.args.get("kw") or "").strip() or None,
        "category_id": request.args.get("category_id", type=int),
        "zone": (request.args.get("zone") or "").strip() or None,
        "status": (request.args.get("status") or "").strip() or None,
        "date_from": _date("date_from"),
        "date_to": _date("date_to"),
        "page": request.args.get("page", 1, type=int) or 1,
        "order": request.args.get("order") or "new",
    }


# ---------------------------------------------------------------- 列表与检索


@bp.get("/found")
def found_list():
    """招领列表：支持关键词模糊搜索 + 分类/分区/状态/时间筛选 + 分页。"""
    page_obj = FoundItemRepository.search(**_search_args())
    return ok(paginated(page_obj, [_found_card(i) for i in page_obj.items]))


@bp.get("/lost")
def lost_list():
    """寻物列表。"""
    page_obj = LostItemRepository.search(**_search_args())
    return ok(paginated(page_obj, [_lost_card(i) for i in page_obj.items]))


@bp.get("/search")
def search():
    """全局模糊搜索：招领与寻物一起搜。"""
    kw = (request.args.get("kw") or "").strip()
    if not kw:
        return fail("请输入搜索关键词")
    page = request.args.get("page", 1, type=int) or 1
    res = item_service.global_search(kw, page)
    return ok({
        "keyword": kw,
        "found": paginated(res["found"], [_found_card(i) for i in res["found"].items]),
        "lost": paginated(res["lost"], [_lost_card(i) for i in res["lost"].items]),
    })


@bp.get("/mine")
@login_required_json
def mine():
    """我的发布。"""
    found = FoundItemRepository.by_founder(current_user.id)
    lost = LostItemRepository.by_owner(current_user.id)
    return ok({
        "found": paginated(found, [_found_card(i) for i in found.items]),
        "lost": paginated(lost, [_lost_card(i) for i in lost.items]),
    })


# ---------------------------------------------------------------- 登记与发布


@bp.post("/found")
@login_required_json
def found_create():
    """拾获登记 → 信息发布：登记后自动跑一次匹配并通知疑似失主。"""
    item = item_service.create_found_item(payload(), current_user, request.files.getlist("images"))
    return ok({"id": item.id, "item": _found_card(item)}, msg=f"拾获登记成功，单号 {item.code}")


@bp.post("/lost")
@login_required_json
def lost_create():
    """寻物启事发布。"""
    item = item_service.create_lost_item(payload(), current_user, request.files.getlist("images"))
    return ok({"id": item.id, "item": _lost_card(item)}, msg=f"寻物启事发布成功，单号 {item.code}")


# ---------------------------------------------------------------- 详情与匹配


@bp.get("/found/<int:item_id>")
def found_detail(item_id):
    """招领详情：含匹配推荐列表与推荐理由明细。"""
    bundle = item_service.item_detail_with_matches("found", item_id, top=5)
    item = bundle["item"]
    item_service.incr_view(item)
    data = _found_card(item, detail=True)
    data["matches"] = [
        {
            "id": m["lost_item"].id,
            "code": m["lost_item"].code,
            "title": m["lost_item"].title,
            "score": m["score"],
            "detail": m["detail"],
            "item": _lost_card(m["lost_item"]),
        }
        for m in bundle["matches"]
    ]
    return ok({"item": data, "can_claim": _can_claim(item)})


@bp.get("/lost/<int:item_id>")
def lost_detail(item_id):
    """寻物详情：推荐可能相关的招领信息。"""
    bundle = item_service.item_detail_with_matches("lost", item_id, top=5)
    item = bundle["item"]
    item_service.incr_view(item)
    data = _lost_card(item)
    data["matches"] = [
        {
            "id": m["found_item"].id,
            "code": m["found_item"].code,
            "title": m["found_item"].title,
            "score": m["score"],
            "detail": m["detail"],
            "item": _found_card(m["found_item"]),
        }
        for m in bundle["matches"]
    ]
    return ok({"item": data})


@bp.get("/found/<int:item_id>/matches")
def found_matches(item_id):
    results = match_service.recommend_for_found(item_id, limit=10)
    return ok({
        "matches": [
            {"score": m["score"], "detail": m["detail"], "item": _lost_card(m["lost_item"])}
            for m in results
        ]
    })


@bp.get("/lost/<int:item_id>/matches")
def lost_matches(item_id):
    results = match_service.recommend_for_lost(item_id, limit=10)
    return ok({
        "matches": [
            {"score": m["score"], "detail": m["detail"], "item": _found_card(m["found_item"])}
            for m in results
        ]
    })


def _can_claim(item) -> bool:
    """前端是否展示"提交认领"按钮。"""
    if not current_user.is_authenticated:
        return False
    if item.founder_id == current_user.id:
        return False
    return item.status == "unclaimed"


# ---------------------------------------------------------------- 编辑与状态


@bp.put("/found/<int:item_id>")
@login_required_json
def found_update(item_id):
    item = FoundItemRepository.get_or_404(item_id)
    if not item_service.can_edit(item, current_user):
        return fail("无权修改他人的登记信息", code=403, status=403)
    item = item_service.update_item(item, payload(), current_user)
    return ok({"item": _found_card(item)}, msg="更新成功")


@bp.put("/lost/<int:item_id>")
@login_required_json
def lost_update(item_id):
    item = LostItemRepository.get_or_404(item_id)
    if not item_service.can_edit(item, current_user):
        return fail("无权修改他人的寻物启事", code=403, status=403)
    item = item_service.update_item(item, payload(), current_user)
    return ok({"item": _lost_card(item)}, msg="更新成功")


@bp.post("/found/<int:item_id>/cancel")
@login_required_json
def found_cancel(item_id):
    item = FoundItemRepository.get_or_404(item_id)
    if not item_service.can_edit(item, current_user):
        return fail("无权撤销他人的登记信息", code=403, status=403)
    item_service.cancel_item(item, current_user)
    return ok(msg="已撤销发布")


@bp.post("/lost/<int:item_id>/cancel")
@login_required_json
def lost_cancel(item_id):
    item = LostItemRepository.get_or_404(item_id)
    if not item_service.can_edit(item, current_user):
        return fail("无权撤销他人的寻物启事", code=403, status=403)
    item_service.cancel_item(item, current_user)
    return ok(msg="已撤销发布")


@bp.post("/found/<int:item_id>/archive")
@login_required_json
def found_archive(item_id):
    """结果归档：仅物品登记人本人、职工或管理员。"""
    item = FoundItemRepository.get_or_404(item_id)
    if not (current_user.is_staff or item.founder_id == current_user.id):
        return fail("仅登记人本人或职工/管理员可归档", code=403, status=403)
    item_service.archive_item(item, current_user)
    return ok(msg="已归档")


@bp.get("/found/<int:item_id>/claims")
def found_claims(item_id):
    """该物品收到的认领申请时间线（脱敏展示）。"""
    item = FoundItemRepository.get_or_404(item_id)
    claims = sorted(item.claims, key=lambda c: c.created_at, reverse=True)
    return ok({
        "claims": [
            {
                "id": c.id,
                "claim_no": c.claim_no,
                "status": c.status,
                "status_label": c.status_label,
                "reason": (c.reason or "")[:60],
                "claimant": user_public(c.claimant),
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for c in claims
        ]
    })


@bp.get("/found/<int:item_id>/can-handle")
@login_required_json
def can_handle(item_id):
    """前端判断能否审核该物品下的认领申请。"""
    item = FoundItemRepository.get_or_404(item_id)
    return ok({"can_handle": current_user.is_staff or item.founder_id == current_user.id})
