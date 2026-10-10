"""消息通知服务：站内信为主，预留邮件/短信通道。"""
from __future__ import annotations

from flask import current_app

from app.extensions import db
from app.models import NOTIFY_CLAIM, NOTIFY_MATCH, NOTIFY_RESULT, NOTIFY_SYSTEM, Notification


def send(
    user_id: int,
    title: str,
    content: str = "",
    type: str = NOTIFY_SYSTEM,
    related_type: str | None = None,
    related_id: int | None = None,
    link: str | None = None,
    commit: bool = True,
) -> Notification:
    """通知发送的唯一出口。link 为前端路由，如 /items/found/12。"""
    n = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        related_type=related_type,
        related_id=related_id,
        link=link,
    )
    db.session.add(n)
    if commit:
        db.session.commit()
    return n


def notify_match(found_item, lost_item, score: float) -> None:
    """匹配到疑似失物 → 通知失主。"""
    send(
        user_id=lost_item.owner_id,
        type=NOTIFY_MATCH,
        title="发现疑似你丢失的物品",
        content=f"系统匹配到一条拾获信息《{found_item.title}》，相似度 {score:.0%}，请核对后发起认领。",
        related_type="found_item",
        related_id=found_item.id,
        link=f"/items/found/{found_item.id}",
    )


def notify_claim_submitted(claim) -> None:
    """有人提交认领 → 通知拾获登记人处理。"""
    send(
        user_id=claim.found_item.founder_id,
        type=NOTIFY_CLAIM,
        title="你的招领信息收到一条认领申请",
        content=f"认领单 {claim.claim_no}：{(claim.reason or '（未填写理由）')[:40]}，请尽快核实。",
        related_type="claim",
        related_id=claim.id,
        link=f"/claims/{claim.id}",
    )


def notify_claim_result(claim, approved: bool, comment: str = "") -> None:
    """认领审核结果 → 通知申请人。"""
    send(
        user_id=claim.claimant_id,
        type=NOTIFY_RESULT,
        title="认领申请" + ("已通过" if approved else "被驳回"),
        content=(f"认领单 {claim.claim_no} 审核结果：{'通过，请按约定时间领取' if approved else '驳回'}。"
                 f"{('处理意见：' + comment) if comment else ''}"),
        related_type="claim",
        related_id=claim.id,
        link=f"/claims/{claim.id}",
    )


def notify_broadcast(user_ids, title: str, content: str) -> int:
    """系统公告广播。"""
    for uid in user_ids:
        send(uid, title, content, type=NOTIFY_SYSTEM, commit=False)
    db.session.commit()
    current_app.logger.info("广播通知 %s 条：%s", len(user_ids), title)
    return len(user_ids)
