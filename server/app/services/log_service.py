"""操作日志服务：全流程可追溯的落点。所有写操作都应调用 record()。"""
from __future__ import annotations

import json
from datetime import UTC, datetime

from flask import current_app, has_request_context, request

from app.extensions import db
from app.models import OperationLog
from app.utils import client_ip


def record(
    action: str,
    user=None,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: dict | None = None,
    result: str = "success",
    commit: bool = True,
):
    """写入一条操作日志。

    :param action: 动作编码，建议 "对象_动作"，如 found_item_create / claim_approve
    :param user: 当前操作用户，None 表示匿名
    日志写入失败绝不阻断主业务。
    """
    ip = ua = None
    if has_request_context():
        ip = client_ip()
        ua = (request.user_agent.string or "")[:255]

    try:
        log = OperationLog(
            user_id=getattr(user, "id", None),
            username=getattr(user, "username", None) or "anonymous",
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=json.dumps(detail or {}, ensure_ascii=False)[:2000],
            ip=ip,
            user_agent=ua,
            result=result,
        )
        db.session.add(log)
        if commit:
            db.session.commit()
        current_app.logger.info("[%s] user=%s target=%s:%s result=%s",
                                action, log.username, target_type, target_id, result)
        return log
    except Exception as exc:
        current_app.logger.warning("写操作日志失败：%s", exc)
        db.session.rollback()
        return None


def record_state_change(obj_label: str, obj_id, old: str, new: str, user=None, extra: dict | None = None):
    """状态变更日志：记录变更前后值，便于追溯责任。"""
    detail = {"from": old, "to": new, "at": datetime.now(UTC).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")}
    if extra:
        detail.update(extra)
    return record(
        action=f"{obj_label}_state_change",
        user=user,
        target_type=obj_label,
        target_id=obj_id,
        detail=detail,
    )
