"""认领确认与状态流转模块。

状态机：
    物品：未认领 → 待确认 → 已认领 → 已归档（终态）；驳回可回退到未认领；发布人可撤销
    认领单：待确认 → 已认领 / 已驳回 / 已取消；已认领 → 已归档（终态）

挂载前缀：/api/v1/claims
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_login import current_user

from app.blueprints import payload, user_public
from app.decorators import login_required_json, staff_required
from app.models import CLAIM_STATUS_LABELS
from app.repositories import ClaimRepository, FoundItemRepository
from app.schemas import fail, ok, paginated
from app.services import claim_service
from app.services.state_machine import ITEM_TRANSITIONS, allowed_actions

bp = Blueprint("claims", __name__)


def _claim_dict(claim) -> dict:
    data = claim.to_dict()
    data["claimant"] = user_public(claim.claimant)
    data["handler"] = user_public(claim.handler)
    data["found_item"] = {
        "id": claim.found_item.id,
        "code": claim.found_item.code,
        "title": claim.found_item.title,
        "status": claim.found_item.status,
        "status_label": claim.found_item.status_label,
        "storage_place": claim.found_item.storage_place,
    }
    return data


# ---------------------------------------------------------------- 提交


@bp.post("/create")
@login_required_json
def create():
    """提交认领：物品 未认领 → 待确认，并通知登记人。"""
    data = payload()
    found_item_id = data.get("found_item_id")
    if not found_item_id:
        return fail("缺少参数 found_item_id")
    try:
        found_item_id = int(found_item_id)
    except (TypeError, ValueError):
        return fail("招领信息 ID 不正确")
    item = FoundItemRepository.get_or_404(found_item_id)
    raw_lost_id = data.get("lost_item_id")
    if raw_lost_id not in (None, ""):
        try:
            lost_item_id = int(raw_lost_id)
        except (TypeError, ValueError):
            return fail("关联寻物启事 ID 不正确，请填写数字编号或留空")
    else:
        lost_item_id = None
    claim = claim_service.submit_claim(item, current_user, data, lost_item_id)
    return ok({"id": claim.id, "claim": _claim_dict(claim)}, msg=f"认领申请已提交，单号 {claim.claim_no}")


# ---------------------------------------------------------------- 查询


@bp.get("/mine")
@login_required_json
def mine():
    """我提交的认领申请。"""
    page_obj = ClaimRepository.by_claimant(current_user.id)
    return ok(paginated(page_obj, [_claim_dict(c) for c in page_obj.items]))


@bp.get("/inbox")
@login_required_json
def inbox():
    """待我处理：我发布的物品收到的申请（职工/管理员可见全部待审）。"""
    page_obj = ClaimRepository.inbox_for_handler(current_user.id)
    return ok(paginated(page_obj, [_claim_dict(c) for c in page_obj.items]))


@bp.get("/pending")
@staff_required
def pending():
    """全部待审认领单（职工/管理员）。"""
    page_obj = ClaimRepository.all_pending()
    return ok(paginated(page_obj, [_claim_dict(c) for c in page_obj.items]))


@bp.get("/<int:claim_id>")
@login_required_json
def detail(claim_id):
    claim = ClaimRepository.get_or_404(claim_id)
    if not (claim.claimant_id == current_user.id
            or current_user.is_staff
            or claim.found_item.founder_id == current_user.id):
        return fail("无权查看该认领单", code=403, status=403)
    data = _claim_dict(claim)
    data["can_handle"] = claim_service.can_handle(claim, current_user)
    data["item_actions"] = allowed_actions(claim.found_item.status)
    return ok({"claim": data})


@bp.get("/meta")
def meta():
    """认领相关字典：状态标签与状态机允许的流转。"""
    return ok({
        "claim_status": CLAIM_STATUS_LABELS,
        "item_transitions": {k: sorted(v) for k, v in ITEM_TRANSITIONS.items()},
    })


# ---------------------------------------------------------------- 状态流转


def _guard(claim_id: int):
    """取出认领单并校验处理权限。"""
    claim = ClaimRepository.get_or_404(claim_id)
    if not claim_service.can_handle(claim, current_user):
        return None, fail("无权处理该认领申请", code=403, status=403)
    return claim, None


@bp.post("/<int:claim_id>/approve")
@login_required_json
def approve(claim_id):
    """审核通过：物品→已认领，同物品其它待审申请自动驳回，关联寻物同步置为已认领。"""
    claim, err = _guard(claim_id)
    if err:
        return err
    data = payload()
    claim = claim_service.approve_claim(claim, current_user, (data.get("comment") or "").strip())
    return ok({"claim": _claim_dict(claim)}, msg="认领已通过，物品状态更新为已认领")


@bp.post("/<int:claim_id>/reject")
@login_required_json
def reject(claim_id):
    """驳回：无其它待审申请时物品回退到未认领，并扣减申请人信用分。"""
    claim, err = _guard(claim_id)
    if err:
        return err
    data = payload()
    comment = (data.get("comment") or "").strip()
    if not comment:
        return fail("驳回必须填写处理意见")
    claim = claim_service.reject_claim(claim, current_user, comment)
    return ok({"claim": _claim_dict(claim)}, msg="认领已驳回")


@bp.post("/<int:claim_id>/cancel")
@login_required_json
def cancel(claim_id):
    """申请人撤回（仅待确认且本人或职工）。"""
    claim = ClaimRepository.get_or_404(claim_id)
    claim = claim_service.cancel_claim(claim, current_user)
    return ok({"claim": _claim_dict(claim)}, msg="已撤回认领申请")


@bp.post("/<int:claim_id>/archive")
@login_required_json
def archive(claim_id):
    """归档结案：认领单→已归档，物品→已归档，关联寻物同步归档。"""
    claim, err = _guard(claim_id)
    if err:
        return err
    claim = claim_service.archive_claim(claim, current_user)
    return ok({"claim": _claim_dict(claim)}, msg="已归档，流程闭环完成")


@bp.get("/trace/<int:claim_id>")
@login_required_json
def trace(claim_id):
    """认领单的全流程操作日志（可追溯性展示）。"""
    from app.repositories import LogRepository

    claim = ClaimRepository.get_or_404(claim_id)
    logs = LogRepository.trace("claim", claim.id)
    return ok({
        "claim_no": claim.claim_no,
        "logs": [
            {
                "action": log.action,
                "username": log.username,
                "detail": log.detail,
                "ip": log.ip,
                "result": log.result,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for log in logs
        ],
    })
