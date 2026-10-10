"""认领确认流程与状态机用例（7 条）。"""
from __future__ import annotations

import pytest

from app.extensions import db
from app.services import claim_service
from app.services.state_machine import (
    ClaimState,
    InvalidTransition,
    ItemState,
    assert_item_transition,
)
from app.schemas import BusinessError


def test_submit_claim_sets_item_pending(app, found_item, student2):
    claim = claim_service.submit_claim(found_item, student2, {"reason": "这是我的水杯，杯盖有磕碰"})
    assert claim.status == ClaimState.PENDING
    db.session.refresh(found_item)
    assert found_item.status == ItemState.PENDING_CONFIRM


def test_cannot_claim_own_item(app, found_item, staff):
    with pytest.raises(BusinessError) as exc:
        claim_service.submit_claim(found_item, staff, {"reason": "认领自己登记的物品应当被拒绝"})
    assert "自己" in str(exc.value)


def test_duplicate_claim_rejected(app, found_item, student2):
    claim_service.submit_claim(found_item, student2, {"reason": "第一次提交认领申请，理由充分"})
    with pytest.raises(BusinessError):
        claim_service.submit_claim(found_item, student2, {"reason": "再次提交认领申请，应当被拒绝"})


def test_approve_sets_claimed_and_rejects_others(app, found_item, student2, student, staff):
    claim_a = claim_service.submit_claim(found_item, student2, {"reason": "认领人甲的理由描述，足够长"})
    found_item.status = ItemState.UNCLAIMED          # 允许第二人并发提交（模拟竞态）
    db.session.commit()
    claim_b = claim_service.submit_claim(found_item, student, {"reason": "认领人乙的理由描述，足够长"})

    claim_service.approve_claim(claim_a, staff, "特征吻合")
    db.session.refresh(found_item)
    db.session.refresh(claim_b)
    assert found_item.status == ItemState.CLAIMED
    assert found_item.claimed_by == student2.id
    assert claim_b.status == ClaimState.REJECTED


def test_reject_rolls_back_to_unclaimed(app, found_item, student2, staff):
    claim = claim_service.submit_claim(found_item, student2, {"reason": "认领理由描述，用于测试驳回"})
    claim_service.reject_claim(claim, staff, "特征不符")
    db.session.refresh(found_item)
    assert found_item.status == ItemState.UNCLAIMED
    assert claim.status == ClaimState.REJECTED


def test_archive_sets_both_archived(app, found_item, student2, staff):
    claim = claim_service.submit_claim(found_item, student2, {"reason": "认领理由描述，用于测试归档"})
    claim_service.approve_claim(claim, staff, "通过")
    claim_service.archive_claim(claim, staff)
    db.session.refresh(found_item)
    assert claim.status == ClaimState.ARCHIVED
    assert found_item.status == ItemState.ARCHIVED


def test_invalid_transition_raises():
    with pytest.raises(InvalidTransition):
        assert_item_transition(ItemState.ARCHIVED, ItemState.CLAIMED)
    with pytest.raises(InvalidTransition):
        assert_item_transition(ItemState.UNCLAIMED, ItemState.ARCHIVED)


def test_submit_with_nonexistent_lost_item_id_rejected(app, found_item, student2):
    """回归：关联寻物启事 ID 不存在时应报业务错误，而非外键 500。"""
    with pytest.raises(BusinessError) as exc:
        claim_service.submit_claim(found_item, student2,
                                   {"reason": "认领理由描述，关联了不存在的寻物启事"},
                                   lost_item_id=999999)
    assert "不存在" in str(exc.value)


# ---------------- 以下为路由级（HTTP）用例，补全 D-02 认领驳回/撤回覆盖 ----------------

def _submit(client, found_item, claimant, login_as):
    """工具：提交认领申请并返回认领单 id（已用 claimant 登录）。"""
    claim = claim_service.submit_claim(found_item, claimant, {"reason": "认领理由描述，用于路由级测试"})
    login_as(claimant)
    return claim.id


def test_reject_via_api_as_staff(app, found_item, student2, staff, client, login_as):
    """路由：楼管驳回待审认领，物品回退未认领。"""
    cid = _submit(client, found_item, student2, login_as)
    login_as(staff)
    resp = client.post(f"/api/v1/claims/{cid}/reject", json={"comment": "特征不符，驳回"})
    assert resp.get_json()["code"] == 0
    claim = claim_service.ClaimRepository.get_or_404(cid)
    db.session.refresh(found_item)
    assert claim.status == ClaimState.REJECTED
    assert found_item.status == ItemState.UNCLAIMED


def test_reject_via_api_requires_staff(app, found_item, student2, client, login_as):
    """路由：普通学生（非处理人）驳回应被拒（403）。"""
    cid = _submit(client, found_item, student2, login_as)
    login_as(student2)  # 申请人本身非职工
    resp = client.post(f"/api/v1/claims/{cid}/reject", json={"comment": "我想驳回"})
    assert resp.get_json()["code"] == 403


def test_reject_via_api_requires_comment(app, found_item, student2, staff, client, login_as):
    """路由：驳回缺少处理意见应被拒。"""
    cid = _submit(client, found_item, student2, login_as)
    login_as(staff)
    resp = client.post(f"/api/v1/claims/{cid}/reject", json={"comment": ""})
    assert resp.get_json()["code"] != 0
    assert "处理意见" in resp.get_json()["msg"]


def test_withdraw_own_claim_via_api(app, found_item, student2, client, login_as):
    """路由：申请人撤回自己的待审认领（撤回/取消）。"""
    cid = _submit(client, found_item, student2, login_as)
    login_as(student2)
    resp = client.post(f"/api/v1/claims/{cid}/cancel")
    assert resp.get_json()["code"] == 0
    claim = claim_service.ClaimRepository.get_or_404(cid)
    db.session.refresh(found_item)
    assert claim.status == ClaimState.CANCELLED
    assert found_item.status == ItemState.UNCLAIMED


def test_withdraw_other_claim_forbidden(app, found_item, student2, student, client, login_as):
    """路由：非本人、非职工撤回他人认领应被拒。"""
    cid = _submit(client, found_item, student2, login_as)
    login_as(student)  # 第三方学生，非职工
    resp = client.post(f"/api/v1/claims/{cid}/cancel")
    assert resp.get_json()["code"] != 0


def test_reject_after_approved_is_invalid(app, found_item, student2, staff):
    """边界：已通过的认领单不能再被驳回（状态机非法流转）。"""
    claim = claim_service.submit_claim(found_item, student2, {"reason": "认领理由，用于非法流转测试"})
    claim_service.approve_claim(claim, staff, "通过")
    with pytest.raises(InvalidTransition):
        claim_service.reject_claim(claim, staff, "反悔驳回")
