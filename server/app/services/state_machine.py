"""状态机建模：物品状态 + 认领单状态。

物品（拾获/寻物）主流程：
    未认领 unclaimed ──提交认领──▶ 待确认 pending ──审核通过──▶ 已认领 claimed ──归档──▶ 已归档 archived
        │                              │
        └──撤销──▶ 已撤销 cancelled ◀──审核驳回（无其它待审申请时回退到未认领）

认领单：
    待确认 pending ──▶ 已认领 approved ──▶ 已归档 archived
                 └────▶ 已驳回 rejected
                 └────▶ 已取消 cancelled
"""
from __future__ import annotations

from typing import Iterable


class ItemState:
    UNCLAIMED = "unclaimed"
    PENDING_CONFIRM = "pending"
    CLAIMED = "claimed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"

    ALL = (UNCLAIMED, PENDING_CONFIRM, CLAIMED, ARCHIVED, CANCELLED)


class ClaimState:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

    ALL = (PENDING, APPROVED, REJECTED, CANCELLED, ARCHIVED)


# 邻接表：key 为当前状态，value 为允许的下一状态集合
ITEM_TRANSITIONS: dict[str, set[str]] = {
    ItemState.UNCLAIMED: {ItemState.PENDING_CONFIRM, ItemState.CANCELLED},
    ItemState.PENDING_CONFIRM: {ItemState.UNCLAIMED, ItemState.CLAIMED, ItemState.CANCELLED},
    ItemState.CLAIMED: {ItemState.ARCHIVED},
    ItemState.ARCHIVED: set(),
    ItemState.CANCELLED: set(),
}

CLAIM_TRANSITIONS: dict[str, set[str]] = {
    ClaimState.PENDING: {ClaimState.APPROVED, ClaimState.REJECTED, ClaimState.CANCELLED},
    ClaimState.APPROVED: {ClaimState.ARCHIVED},
    ClaimState.REJECTED: set(),
    ClaimState.CANCELLED: set(),
    ClaimState.ARCHIVED: set(),
}


class InvalidTransition(ValueError):
    """非法状态流转异常，表现层捕获后统一返回 400。"""

    def __init__(self, obj: str, current: str, target: str, allowed: Iterable[str]):
        self.obj, self.current, self.target = obj, current, target
        self.allowed = sorted(allowed)
        super().__init__(
            f"{obj} 状态流转非法：{current} → {target}，"
            f"允许的下一状态为 {self.allowed or '（终态，不可流转）'}"
        )


def can_transit(table: dict[str, set[str]], current: str, target: str) -> bool:
    return target in table.get(current, set())


def assert_item_transition(current: str, target: str) -> None:
    if not can_transit(ITEM_TRANSITIONS, current, target):
        raise InvalidTransition("物品", current, target, ITEM_TRANSITIONS.get(current, set()))


def assert_claim_transition(current: str, target: str) -> None:
    if not can_transit(CLAIM_TRANSITIONS, current, target):
        raise InvalidTransition("认领单", current, target, CLAIM_TRANSITIONS.get(current, set()))


def next_states(table: dict[str, set[str]], current: str) -> list[str]:
    return sorted(table.get(current, set()))


# 业务动作 → 状态变更映射（前端按钮按当前状态渲染）
ITEM_ACTIONS: dict[str, dict] = {
    "submit_claim": {"from": ItemState.UNCLAIMED, "to": ItemState.PENDING_CONFIRM, "label": "提交认领"},
    "approve": {"from": ItemState.PENDING_CONFIRM, "to": ItemState.CLAIMED, "label": "审核通过"},
    "reject": {"from": ItemState.PENDING_CONFIRM, "to": ItemState.UNCLAIMED, "label": "驳回"},
    "archive": {"from": ItemState.CLAIMED, "to": ItemState.ARCHIVED, "label": "归档结案"},
    "cancel": {"from": ItemState.UNCLAIMED, "to": ItemState.CANCELLED, "label": "撤销发布"},
}


def allowed_actions(current: str) -> list[str]:
    return [name for name, rule in ITEM_ACTIONS.items() if rule["from"] == current]
