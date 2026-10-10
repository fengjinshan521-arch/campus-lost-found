"""后台管理与数据统计：概览、认领率、分布、趋势、高发地点、处理时长。"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models import Category, Claim, FoundItem, LostItem, MatchRecord, OperationLog, User
from app.services.state_machine import ClaimState, ItemState


def overview() -> dict:
    return {
        "found_total": FoundItem.query.count(),
        "lost_total": LostItem.query.count(),
        "found_unclaimed": FoundItem.query.filter_by(status=ItemState.UNCLAIMED).count(),
        "found_pending": FoundItem.query.filter_by(status=ItemState.PENDING_CONFIRM).count(),
        "found_claimed": FoundItem.query.filter_by(status=ItemState.CLAIMED).count(),
        "found_archived": FoundItem.query.filter_by(status=ItemState.ARCHIVED).count(),
        "lost_open": LostItem.query.filter(
            LostItem.status.in_([ItemState.UNCLAIMED, ItemState.PENDING_CONFIRM])).count(),
        "claim_total": Claim.query.count(),
        "claim_pending": Claim.query.filter_by(status=ClaimState.PENDING).count(),
        "claim_approved": Claim.query.filter_by(status=ClaimState.APPROVED).count(),
        "user_total": User.query.count(),
        "match_total": MatchRecord.query.count(),
    }


def claim_rate() -> dict:
    o = overview()
    done = o["found_claimed"] + o["found_archived"]
    active = done + o["found_unclaimed"] + o["found_pending"]
    return {
        "done": done,
        "active": active,
        "rate": round(done / active, 4) if active else 0.0,
        "rate_percent": f"{(done / active * 100):.1f}%" if active else "0.0%",
    }


def category_distribution() -> list[dict]:
    result = []
    for c in Category.query.filter_by(is_active=True).all():
        result.append({
            "id": c.id,
            "name": c.name,
            "found": FoundItem.query.filter_by(category_id=c.id).count(),
            "lost": LostItem.query.filter_by(category_id=c.id).count(),
        })
    return sorted(result, key=lambda x: x["found"] + x["lost"], reverse=True)


def trend(days: int = 14) -> list[dict]:
    today = datetime.now(UTC).replace(tzinfo=None).date()
    out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        nxt = d + timedelta(days=1)
        out.append({
            "date": d.strftime("%m-%d"),
            "found": FoundItem.query.filter(FoundItem.created_at >= d, FoundItem.created_at < nxt).count(),
            "lost": LostItem.query.filter(LostItem.created_at >= d, LostItem.created_at < nxt).count(),
        })
    return out


def hot_locations(top: int = 8) -> list[dict]:
    counter: Counter = Counter()
    for f in FoundItem.query.all():
        if f.found_zone:
            counter[f.found_zone] += 1
    for l in LostItem.query.all():
        if l.lost_zone:
            counter[l.lost_zone] += 1
    return [{"zone": z, "count": c} for z, c in counter.most_common(top)]


def avg_handle_hours() -> float:
    rows = Claim.query.filter(Claim.handled_at.isnot(None), Claim.created_at.isnot(None)).all()
    if not rows:
        return 0.0
    total = sum((c.handled_at - c.created_at).total_seconds() for c in rows)
    return round(total / len(rows) / 3600.0, 2)


def status_pipeline() -> list[dict]:
    labels = {
        ItemState.UNCLAIMED: "未认领",
        ItemState.PENDING_CONFIRM: "待确认",
        ItemState.CLAIMED: "已认领",
        ItemState.ARCHIVED: "已归档",
        ItemState.CANCELLED: "已撤销",
    }
    counts = dict(db.session.query(FoundItem.status, func.count(FoundItem.id))
                  .group_by(FoundItem.status).all())
    return [{"status": k, "label": labels.get(k, k), "count": counts.get(k, 0)} for k in labels]


def active_users(top: int = 10) -> list[dict]:
    counter: defaultdict = defaultdict(int)
    for f in FoundItem.query.all():
        counter[f.founder_id] += 1
    for l in LostItem.query.all():
        counter[l.owner_id] += 1
    for c in Claim.query.all():
        counter[c.claimant_id] += 1
    out = []
    for uid, cnt in sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:top]:
        u = db.session.get(User, uid)
        if u:
            out.append({"username": u.username, "role": u.role_label, "actions": cnt})
    return out


def recent_logs(limit: int = 10):
    return OperationLog.query.order_by(OperationLog.created_at.desc()).limit(limit).all()
