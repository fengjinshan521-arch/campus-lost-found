"""消息通知模块：站内信列表、未读数、标记已读。

挂载前缀：/api/v1/notifications
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_login import current_user

from app.decorators import login_required_json
from app.extensions import db
from app.models import Notification
from app.repositories import NotificationRepository
from app.schemas import fail, ok, paginated

bp = Blueprint("notify", __name__)


def _notify_dict(n) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "content": n.content,
        "related_type": n.related_type,
        "related_id": n.related_id,
        "link": n.link,
        "is_read": n.is_read,
        "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@bp.get("/")
@login_required_json
def index():
    """我的通知列表（?unread=1 只看未读）。"""
    unread_only = request.args.get("unread") in ("1", "true", "yes")
    page_obj = NotificationRepository.for_user(current_user.id, unread_only=unread_only)
    return ok({
        "unread_count": NotificationRepository.unread_count(current_user.id),
        "list": paginated(page_obj, [_notify_dict(n) for n in page_obj.items]),
    })


@bp.get("/unread-count")
@login_required_json
def unread_count():
    return ok({"unread_count": NotificationRepository.unread_count(current_user.id)})


@bp.post("/<int:notify_id>/read")
@login_required_json
def mark_read(notify_id):
    n = db.session.get(Notification, notify_id)
    if n is None:
        return fail("通知不存在", status=404)
    if n.user_id != current_user.id:
        return fail("无权操作他人的通知", code=403, status=403)
    n.mark_read()
    return ok({"id": n.id}, msg="已标记已读")


@bp.post("/read-all")
@login_required_json
def read_all():
    rows = NotificationRepository.for_user(current_user.id, unread_only=True)
    count = 0
    for n in rows.items:
        n.mark_read(commit=False)
        count += 1
    db.session.commit()
    return ok({"updated": count}, msg=f"已将 {count} 条通知标记为已读")
