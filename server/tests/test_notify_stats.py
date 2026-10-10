"""消息通知、数据统计与日志追溯用例（4 条）。"""
from __future__ import annotations

from app.repositories import NotificationRepository
from app.services import claim_service, stats_service
from app.services import log_service


def test_claim_submitted_notifies_founder(app, found_item, student2):
    claim_service.submit_claim(found_item, student2, {"reason": "这是我的杯子，杯盖磕碰痕迹一致"})
    assert NotificationRepository.unread_count(found_item.founder_id) >= 1


def test_approve_notifies_claimant(app, found_item, student2, staff):
    claim = claim_service.submit_claim(found_item, student2, {"reason": "认领理由描述，用于测试通知"})
    before = NotificationRepository.unread_count(student2.id)
    claim_service.approve_claim(claim, staff, "特征吻合")
    assert NotificationRepository.unread_count(student2.id) > before


def test_unread_count_and_mark_read(app, found_item, student2):
    claim_service.submit_claim(found_item, student2, {"reason": "认领理由描述，用于统计未读数"})
    total = NotificationRepository.unread_count(found_item.founder_id)
    assert total >= 1
    page = NotificationRepository.for_user(found_item.founder_id)
    page.items[0].mark_read()
    assert NotificationRepository.unread_count(found_item.founder_id) == total - 1


def test_overview_and_claim_rate(app, found_item, student2, staff):
    claim = claim_service.submit_claim(found_item, student2, {"reason": "认领理由描述，用于统计认领率"})
    claim_service.approve_claim(claim, staff, "通过")
    overview = stats_service.overview()
    rate = stats_service.claim_rate()
    assert overview["found_total"] == 1
    assert overview["claim_approved"] == 1
    assert rate["rate"] == 1.0
    assert len(stats_service.status_pipeline()) == 5
    assert len(stats_service.trend(7)) == 7
    assert log_service.record("unit_test", staff, "found_item", found_item.id, {"ok": True})
