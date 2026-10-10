"""失物登记、寻物发布与分类检索模块用例（9 条）。"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.services import item_service
from app.services.state_machine import ItemState
from conftest import found_payload, lost_payload

from app.schemas import BusinessError
import pytest


def test_create_found_generates_code_and_zone(app, category, staff):
    item = item_service.create_found_item(found_payload(category), staff)
    assert item.code.startswith("LF-")
    assert item.found_zone == "图书馆"          # 地点归一化生效
    assert item.status == ItemState.UNCLAIMED
    assert item.keywords                        # 检索关键词已抽取


def test_create_lost_success(app, category, student):
    item = item_service.create_lost_item(lost_payload(category), student)
    assert item.code.startswith("XS-")
    assert item.lost_zone == "图书馆"
    assert item.owner_id == student.id


def test_missing_title_rejected(app, category, staff):
    with pytest.raises(BusinessError):
        item_service.create_found_item(found_payload(category, title=""), staff)


def test_missing_time_rejected(app, category, staff):
    with pytest.raises(BusinessError):
        item_service.create_found_item(found_payload(category, happen_time="not-a-time"), staff)


def test_search_hits_title(app, category, staff):
    item_service.create_found_item(found_payload(category), staff)
    resp = app.test_client().get("/api/v1/items/found?kw=iPhone13")
    assert resp.get_json()["data"]["total"] >= 1


def test_search_hits_description(app, category, student):
    item_service.create_lost_item(lost_payload(category), student)
    resp = app.test_client().get("/api/v1/items/lost?kw=裂痕")
    assert resp.get_json()["data"]["total"] >= 1


def test_filter_by_category(app, category, category_other, staff):
    item_service.create_found_item(found_payload(category), staff)
    item_service.create_found_item(found_payload(category_other, title="捡到灰色围巾",
                                                 place="东门校车站"), staff)
    resp = app.test_client().get(f"/api/v1/items/found?category_id={category_other.id}")
    data = resp.get_json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["title"] == "捡到灰色围巾"


def test_empty_result_pagination_ok(app, category):
    resp = app.test_client().get("/api/v1/items/found?kw=不存在的关键词xyz")
    data = resp.get_json()["data"]
    assert data["total"] == 0 and data["items"] == []


def test_non_owner_cannot_edit_via_api(client, login_as, found_item, student2):
    login_as(student2)
    resp = client.put(f"/api/v1/items/found/{found_item.id}", json={"title": "被篡改的标题"})
    assert resp.status_code == 403
    db.session.refresh(found_item)
    assert found_item.title != "被篡改的标题"


def test_view_count_increases(app, found_item):
    before = found_item.view_count
    app.test_client().get(f"/api/v1/items/found/{found_item.id}")
    db.session.refresh(found_item)
    assert found_item.view_count == before + 1
