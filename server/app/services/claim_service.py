"""认领确认流程：提交 → 审核（通过/驳回）→ 交付 → 归档，全程状态机校验 + 留痕。"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models import Claim, FoundItem, LostItem, User
from app.models.claim import CLAIM_TYPE_MATCH, CLAIM_TYPE_SELF
from app.repositories import ClaimRepository
from app.schemas import BusinessError
from app.services import log_service, notify_service
from app.services.state_machine import (
    ClaimState,
    ItemState,
    assert_claim_transition,
    assert_item_transition,
)
from app.utils import generate_code


class ClaimError(BusinessError):
    default_msg = "认领处理失败"


def _next_claim_no() -> str:
    return generate_code("RQ", Claim.query.count() + 1)


def submit_claim(found_item: FoundItem, claimant: User, data: dict,
                 lost_item_id: int | None = None) -> Claim:
    """提交认领：物品 未认领 → 待确认。"""
    if found_item.founder_id == claimant.id:
        raise ClaimError("不能认领自己登记的拾获物品")
    if found_item.status != ItemState.UNCLAIMED:
        raise ClaimError(f"该物品当前状态为「{found_item.status_label}」，暂不可提交认领")
    dup = Claim.query.filter_by(found_item_id=found_item.id, claimant_id=claimant.id,
                                status=ClaimState.PENDING).first()
    if dup:
        raise ClaimError("你已提交过认领申请，请等待处理")

    reason = (data.get("reason") or "").strip()
    if len(reason) < 5:
        raise ClaimError("请填写至少 5 个字的认领理由或物品特征，便于核实")

    if lost_item_id is not None:
        lost = db.session.get(LostItem, lost_item_id)
        if lost is None:
            raise ClaimError(
                f"关联的寻物启事 #{lost_item_id} 不存在，请核对编号或清空该栏后再提交")
        lost_item_id = lost.id

    claim = Claim(
        claim_no=_next_claim_no(),
        found_item_id=found_item.id,
        lost_item_id=lost_item_id,
        claimant_id=claimant.id,
        claim_type=CLAIM_TYPE_MATCH if lost_item_id else (data.get("claim_type") or CLAIM_TYPE_SELF),
        status=ClaimState.PENDING,
        reason=reason,
        contact=(data.get("contact") or "").strip(),
        evidence=json.dumps(list(data.get("evidence") or []), ensure_ascii=False),
    )
    db.session.add(claim)
    db.session.flush()

    assert_item_transition(found_item.status, ItemState.PENDING_CONFIRM)
    found_item.status = ItemState.PENDING_CONFIRM
    db.session.commit()

    log_service.record("claim_submit", claimant, "claim", claim.id,
                       {"claim_no": claim.claim_no, "found_item": found_item.code})
    notify_service.notify_claim_submitted(claim)
    return claim


def approve_claim(claim: Claim, handler: User, comment: str = "") -> Claim:
    """审核通过：认领单→已认领；物品→已认领；其余待审申请自动驳回。"""
    assert_claim_transition(claim.status, ClaimState.APPROVED)
    item = claim.found_item
    assert_item_transition(item.status, ItemState.CLAIMED)

    claim.status = ClaimState.APPROVED
    claim.handler_id = handler.id
    claim.handle_comment = comment
    claim.handled_at = datetime.now(UTC).replace(tzinfo=None)

    item.status = ItemState.CLAIMED
    item.claimed_by = claim.claimant_id
    item.claimed_at = datetime.now(UTC).replace(tzinfo=None)

    for other in ClaimRepository.pending_for_item(item.id):
        if other.id == claim.id:
            continue
        other.status = ClaimState.REJECTED
        other.handler_id = handler.id
        other.handle_comment = "该物品已由他人认领"
        other.handled_at = datetime.now(UTC).replace(tzinfo=None)

    if claim.lost_item_id:
        lost = db.session.get(LostItem, claim.lost_item_id)
        if lost and lost.status in (ItemState.UNCLAIMED, ItemState.PENDING_CONFIRM):
            lost.status = ItemState.CLAIMED
            lost.matched_found_id = item.id
            notify_service.send(
                lost.owner_id, "寻物启事已匹配成功",
                f"你的寻物启事《{lost.title}》已确认找到，认领单 {claim.claim_no}。",
                related_type="lost_item", related_id=lost.id,
                link=f"/items/lost/{lost.id}", commit=False,
            )

    db.session.commit()
    log_service.record("claim_approve", handler, "claim", claim.id,
                       {"claim_no": claim.claim_no, "item_code": item.code, "comment": comment})
    notify_service.notify_claim_result(claim, approved=True, comment=comment)
    return claim


def reject_claim(claim: Claim, handler: User, comment: str = "") -> Claim:
    """驳回：认领单→已驳回；无其它待审申请时物品回退到未认领，并扣信用分。"""
    assert_claim_transition(claim.status, ClaimState.REJECTED)
    claim.status = ClaimState.REJECTED
    claim.handler_id = handler.id
    claim.handle_comment = comment
    claim.handled_at = datetime.now(UTC).replace(tzinfo=None)

    item = claim.found_item
    if item.status == ItemState.PENDING_CONFIRM and not ClaimRepository.pending_for_item(item.id):
        assert_item_transition(item.status, ItemState.UNCLAIMED)
        item.status = ItemState.UNCLAIMED

    claimant = db.session.get(User, claim.claimant_id)
    if claimant:
        claimant.credit_score = max(0, (claimant.credit_score or 100) - 2)

    db.session.commit()
    log_service.record("claim_reject", handler, "claim", claim.id,
                       {"claim_no": claim.claim_no, "comment": comment})
    notify_service.notify_claim_result(claim, approved=False, comment=comment)
    return claim


def cancel_claim(claim: Claim, user: User) -> Claim:
    """申请人撤回（仅待确认状态、仅本人或职工）。"""
    if claim.claimant_id != user.id and not user.is_staff:
        raise ClaimError("无权撤回他人的认领申请")
    assert_claim_transition(claim.status, ClaimState.CANCELLED)
    claim.status = ClaimState.CANCELLED

    item = claim.found_item
    if not ClaimRepository.pending_for_item(item.id):
        assert_item_transition(item.status, ItemState.UNCLAIMED)
        item.status = ItemState.UNCLAIMED
    db.session.commit()
    log_service.record("claim_cancel", user, "claim", claim.id, {"claim_no": claim.claim_no})
    return claim


def archive_claim(claim: Claim, handler: User) -> Claim:
    """归档结案：认领单→已归档；物品→已归档；关联寻物同步归档。"""
    assert_claim_transition(claim.status, ClaimState.ARCHIVED)
    item = claim.found_item
    assert_item_transition(item.status, ItemState.ARCHIVED)

    claim.status = ClaimState.ARCHIVED
    claim.archived_at = datetime.now(UTC).replace(tzinfo=None)
    claim.handler_id = claim.handler_id or handler.id
    item.status = ItemState.ARCHIVED
    item.archived_at = datetime.now(UTC).replace(tzinfo=None)

    if claim.lost_item_id:
        lost = db.session.get(LostItem, claim.lost_item_id)
        if lost and lost.status == ItemState.CLAIMED:
            lost.status = ItemState.ARCHIVED
            lost.archived_at = datetime.now(UTC).replace(tzinfo=None)

    db.session.commit()
    log_service.record("claim_archive", handler, "claim", claim.id, {"claim_no": claim.claim_no})
    return claim


def can_handle(claim: Claim, user: User) -> bool:
    """处理权限：物品登记人本人、职工或管理员。"""
    if not user or not user.is_authenticated:
        return False
    return user.is_staff or claim.found_item.founder_id == user.id


def auto_notify_overdue(hours: int = 72) -> int:
    """超时未处理的认领提醒（可挂定时任务）。"""
    deadline = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours)
    stale = Claim.query.filter(Claim.status == ClaimState.PENDING,
                               Claim.created_at <= deadline).all()
    for c in stale:
        notify_service.send(
            c.found_item.founder_id, "认领申请超时提醒",
            f"认领单 {c.claim_no} 已等待超过 {hours} 小时，请尽快处理。",
            related_type="claim", related_id=c.id, link=f"/claims/{c.id}", commit=False,
        )
    db.session.commit()
    if stale:
        current_app.logger.info("超时认领提醒 %s 条", len(stale))
    return len(stale)
