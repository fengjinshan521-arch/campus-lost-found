"""失物登记 / 拾获登记 / 发布 / 检索 的业务逻辑。"""
from __future__ import annotations

import json
from datetime import UTC, date, datetime

from flask import current_app
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models import Attachment, FoundItem, LostItem, User
from app.models.item import ITEM_STATUS_LABELS
from app.repositories import FoundItemRepository, LostItemRepository
from app.schemas import BusinessError
from app.services import log_service, notify_service
from app.services.state_machine import ItemState, assert_item_transition
from app.utils import build_keywords, client_ip, generate_code, normalize_zone, save_upload


class ItemError(BusinessError):
    default_msg = "物品信息处理失败"


# ---------------------------------------------------------------- 入参处理


def _to_datetime(value):
    """兼容 datetime / date / 字符串（前端 datepicker 常见格式）。"""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def _normalize_features(raw) -> str:
    """特征标签：支持列表或逗号分隔字符串，统一存 JSON 数组。"""
    if not raw:
        return "[]"
    parts = raw if isinstance(raw, list) else [p.strip() for p in str(raw).replace("，", ",").split(",")]
    parts = [str(p).strip() for p in parts if str(p).strip()]
    return json.dumps(parts[:10], ensure_ascii=False)


def _next_code(model, prefix: str) -> str:
    return generate_code(prefix, model.query.count() + 1)


def _save_attachments(files, entity_type: str, entity_id: int, user) -> list[str]:
    urls = []
    for f in files or []:
        if not isinstance(f, FileStorage) or not f.filename:
            continue
        rel_url, orig, size, checksum = save_upload(f, subdir=entity_type)
        db.session.add(Attachment(
            entity_type=entity_type, entity_id=entity_id, uploader_id=user.id,
            original_name=orig, saved_name=rel_url.rsplit("/", 1)[-1],
            rel_path=rel_url, size=size, checksum=checksum,
        ))
        urls.append(rel_url)
    return urls


# ---------------------------------------------------------------- 登记与发布


def create_found_item(data: dict, user: User, files=None) -> FoundItem:
    """拾获登记 → 信息发布。登记后自动跑一次匹配并通知疑似失主。"""
    title = (data.get("title") or "").strip()
    place = (data.get("place") or "").strip()
    happen_time = _to_datetime(data.get("happen_time"))
    category_id = data.get("category_id")

    if not title:
        raise ItemError("标题不能为空")
    if not place:
        raise ItemError("拾获地点不能为空")
    if happen_time is None:
        raise ItemError("拾获时间不能为空或格式不正确")
    if not category_id:
        raise ItemError("请选择物品分类")

    features = _normalize_features(data.get("features"))
    item = FoundItem(
        code=_next_code(FoundItem, "LF"),
        founder_id=user.id,
        category_id=int(category_id),
        title=title,
        description=(data.get("description") or "").strip(),
        features=features,
        found_place=place,
        found_zone=normalize_zone(place),
        found_time=happen_time,
        storage_place=(data.get("storage_place") or "").strip() or "待分配保管点",
        is_sensitive=bool(data.get("is_sensitive")),
        status=ItemState.UNCLAIMED,
    )
    item.keywords = build_keywords(item.title, item.description, place, " ".join(item.feature_list))
    db.session.add(item)
    db.session.flush()   # 先拿 id，再存附件

    images = list(data.get("images") or [])
    images += _save_attachments(files, "found_item", item.id, user)
    item.images = json.dumps(images, ensure_ascii=False)

    db.session.commit()
    log_service.record("found_item_create", user, "found_item", item.id,
                       {"code": item.code, "title": item.title, "zone": item.found_zone})

    try:
        from app.services.match_service import recommend_for_found
        for r in recommend_for_found(item.id, limit=5):
            notify_service.notify_match(item, r["lost_item"], r["score"])
    except Exception as exc:
        current_app.logger.warning("登记后自动匹配失败：%s", exc)
    return item


def create_lost_item(data: dict, user: User, files=None) -> LostItem:
    """寻物启事发布。"""
    title = (data.get("title") or "").strip()
    place = (data.get("place") or "").strip()
    happen_time = _to_datetime(data.get("happen_time"))
    category_id = data.get("category_id")

    if not title:
        raise ItemError("标题不能为空")
    if not place:
        raise ItemError("丢失地点不能为空")
    if happen_time is None:
        raise ItemError("丢失时间不能为空或格式不正确")
    if not category_id:
        raise ItemError("请选择物品分类")

    item = LostItem(
        code=_next_code(LostItem, "XS"),
        owner_id=user.id,
        category_id=int(category_id),
        title=title,
        description=(data.get("description") or "").strip(),
        features=_normalize_features(data.get("features")),
        lost_place=place,
        lost_zone=normalize_zone(place),
        lost_time=happen_time,
        reward=(data.get("reward") or "").strip(),
        is_urgent=bool(data.get("is_urgent")),
        status=ItemState.UNCLAIMED,
    )
    item.keywords = build_keywords(item.title, item.description, place, " ".join(item.feature_list))
    db.session.add(item)
    db.session.flush()

    images = list(data.get("images") or [])
    images += _save_attachments(files, "lost_item", item.id, user)
    item.images = json.dumps(images, ensure_ascii=False)

    db.session.commit()
    log_service.record("lost_item_create", user, "lost_item", item.id,
                       {"code": item.code, "title": item.title})
    return item


# ---------------------------------------------------------------- 更新与状态


def update_item(item, data: dict, user: User):
    before = {"title": item.title, "description": item.description}
    item.title = (data.get("title") or item.title).strip()
    if "description" in data:
        item.description = (data.get("description") or "").strip()
    if "features" in data:
        item.features = _normalize_features(data.get("features"))
    if "category_id" in data and data.get("category_id"):
        item.category_id = int(data["category_id"])
    place = getattr(item, "found_place", None) or getattr(item, "lost_place", None)
    item.keywords = build_keywords(item.title, item.description, place, " ".join(item.feature_list))
    db.session.commit()
    log_service.record("item_update", user, type(item).__name__.lower(), item.id,
                       {"before": before, "after": {"title": item.title}})
    return item


def change_status(item, new_status: str, user: User, reason: str = ""):
    """统一的状态变更入口：先过状态机校验，再落日志。"""
    old = item.status
    assert_item_transition(old, new_status)
    item.status = new_status
    if new_status == ItemState.CLAIMED:
        item.claimed_at = datetime.now(UTC).replace(tzinfo=None)
    if new_status == ItemState.ARCHIVED:
        item.archived_at = datetime.now(UTC).replace(tzinfo=None)
    db.session.commit()
    label = "found_item" if isinstance(item, FoundItem) else "lost_item"
    log_service.record_state_change(label, item.id, old, new_status, user,
                                    {"reason": reason, "ip": client_ip()})
    return item


def cancel_item(item, user: User):
    return change_status(item, ItemState.CANCELLED, user, reason="发布人撤销")


def archive_item(item, user: User):
    return change_status(item, ItemState.ARCHIVED, user, reason="结果归档")


def can_edit(item, user: User) -> bool:
    owner_id = getattr(item, "founder_id", None) or getattr(item, "owner_id", None)
    return bool(user and user.is_authenticated and (owner_id == user.id or user.is_staff))


def can_view_sensitive(item, user: User) -> bool:
    """敏感物品（证件类）：仅所有者、职工、管理员可见完整信息。"""
    if not getattr(item, "is_sensitive", False):
        return True
    return can_edit(item, user)


# ---------------------------------------------------------------- 详情与检索


def incr_view(item) -> None:
    item.view_count = (item.view_count or 0) + 1
    db.session.commit()


def item_detail_with_matches(kind: str, item_id: int, top: int = 5) -> dict:
    from app.services.match_service import recommend_for_found, recommend_for_lost

    if kind == "found":
        item = FoundItemRepository.get_or_404(item_id)
        matches, key = recommend_for_found(item_id, limit=top), "lost_item"
    else:
        item = LostItemRepository.get_or_404(item_id)
        matches, key = recommend_for_lost(item_id, limit=top), "found_item"
    return {
        "item": item,
        "kind": kind,
        "matches": matches,
        "match_key": key,
        "status_label": ITEM_STATUS_LABELS.get(item.status, item.status),
    }


def global_search(keyword: str, page: int = 1) -> dict:
    """全局模糊搜索：招领与寻物同时搜。"""
    return {
        "keyword": keyword,
        "found": FoundItemRepository.search(keyword=keyword, page=page),
        "lost": LostItemRepository.search(keyword=keyword, page=page),
    }
