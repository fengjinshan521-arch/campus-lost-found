"""匹配推荐加权算法用例（6 条）。"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.extensions import db
from app.models import MatchRecord
from app.services import match_service
from app.services.match_service import (
    compute_score,
    factor_location,
    factor_time,
    recommend_for_found,
)
from conftest import found_payload, lost_payload


def _pair(app, category, staff, student, found_over=None, lost_over=None):
    from app.services import item_service

    found = item_service.create_found_item(found_payload(category, **(found_over or {})), staff)
    lost = item_service.create_lost_item(lost_payload(category, **(lost_over or {})), student)
    return found, lost


def test_same_category_same_zone_scores_high(app, category, staff, student):
    found, lost = _pair(app, category, staff, student)
    score, _ = compute_score(found, lost)
    assert score >= 0.7


def test_different_category_scores_low(app, category, category_other, staff, student):
    from app.services import item_service

    found = item_service.create_found_item(found_payload(category), staff)
    lost = item_service.create_lost_item(
        lost_payload(category_other, title="丢失灰色羊毛围巾", place="东门校车站",
                     description="灰色围巾，边缘有流苏，去年冬天买的",
                     features=["灰色", "围巾"],
                     happen_time=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=20)),
        student)
    score, detail = compute_score(found, lost)
    assert detail["factors"]["category"] == 0.0
    assert score < 0.45


def test_time_decay_monotonic(app, category, staff, student):
    from app.services import item_service

    found = item_service.create_found_item(
        found_payload(category, happen_time=datetime.now(UTC).replace(tzinfo=None)), staff)
    near = item_service.create_lost_item(
        lost_payload(category, happen_time=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)), student)
    far = item_service.create_lost_item(
        lost_payload(category, happen_time=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30),
                     title="丢失另一部黑色 iPhone13", place="校门", features=["黑色"]), student)
    assert factor_time(found, near) > factor_time(found, far)


def test_adjacent_zone_partial_score(app, category, staff, student):
    from app.services import item_service

    found = item_service.create_found_item(found_payload(category, place="三教305"), staff)
    lost_adj = item_service.create_lost_item(lost_payload(category, place="图书馆"), student)
    lost_far = item_service.create_lost_item(lost_payload(category, place="东门校车站"), student)
    assert factor_location(found, lost_adj) > factor_location(found, lost_far)


def test_below_threshold_not_recommended(app, category, staff, student):
    from app.services import item_service

    item_service.create_found_item(
        found_payload(category, title="捡到一只灰色袜子", description="纯棉袜子一只",
                      features=["灰色", "袜子"]), staff)
    item_service.create_lost_item(
        lost_payload(category, title="丢失笔记本电脑", description="ThinkPad X1 黑色",
                     features=["黑色", "笔记本"], place="东门校车站"), student)
    results = recommend_for_found(1, limit=10)
    assert results == []


def test_upsert_is_idempotent(app, category, staff, student):
    found, lost = _pair(app, category, staff, student)
    match_service.score_pair(found, lost)
    match_service.score_pair(found, lost)
    match_service.score_pair(found, lost)
    assert MatchRecord.query.filter_by(found_item_id=found.id, lost_item_id=lost.id).count() == 1
