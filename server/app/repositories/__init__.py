"""数据访问层（Repository）：集中封装查询，业务层不写裸 Query。

收益：检索条件集中维护便于加索引；便于单测替换；业务层代码可读。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from app.extensions import db
from app.models import (
    Attachment,
    Category,
    Claim,
    FoundItem,
    LoginAttempt,
    LostItem,
    MatchRecord,
    Notification,
    OperationLog,
    User,
)
from app.models.user import ROLE_ADMIN, ROLE_STAFF
from app.services.state_machine import ClaimState, ItemState
from app.utils import paginate


class BaseRepository:
    model = None

    @classmethod
    def get(cls, pk):
        return db.session.get(cls.model, pk)

    @classmethod
    def get_or_404(cls, pk):
        from flask import abort

        obj = cls.get(pk)
        if obj is None:
            abort(404)
        return obj

    @classmethod
    def query(cls):
        return cls.model.query

    @classmethod
    def count(cls, **filters) -> int:
        return cls.model.query.filter_by(**filters).count()

    @classmethod
    def add(cls, obj, commit: bool = True):
        db.session.add(obj)
        if commit:
            db.session.commit()
        return obj


class UserRepository(BaseRepository):
    model = User

    @classmethod
    def by_username(cls, username: str):
        return User.query.filter_by(username=username).first()

    @classmethod
    def by_email(cls, email: str):
        return User.query.filter_by(email=email).first()

    @classmethod
    def by_student_no(cls, no: str):
        return User.query.filter_by(student_no=no).first()

    @classmethod
    def by_reset_token(cls, token: str):
        return User.query.filter_by(reset_token=token).first()

    @classmethod
    def search(cls, keyword=None, role=None, status=None, page=1):
        q = User.query
        if keyword:
            like = f"%{keyword}%"
            q = q.filter(db.or_(User.username.like(like),
                                User.real_name.like(like),
                                User.student_no.like(like)))
        if role:
            q = q.filter(User.role == role)
        if status:
            q = q.filter(User.status == status)
        return paginate(q.order_by(User.created_at.desc()), page)

    @classmethod
    def staff_and_admins(cls):
        return User.query.filter(User.role.in_([ROLE_STAFF, ROLE_ADMIN])).all()

    @classmethod
    def search_managers(cls, keyword=None, role=None, status=None, page=1):
        """管理人员（楼管 + 系统管理员）分页检索。

        与学生用户列表分开：后台「管理员管理」只面向管理侧账号，避免误操作普通学生。
        """
        q = User.query.filter(User.role.in_([ROLE_STAFF, ROLE_ADMIN]))
        if keyword:
            like = f"%{keyword}%"
            q = q.filter(db.or_(User.username.like(like),
                                User.real_name.like(like),
                                User.phone.like(like)))
        if role in (ROLE_STAFF, ROLE_ADMIN):
            q = q.filter(User.role == role)
        if status:
            q = q.filter(User.status == status)
        return paginate(q.order_by(User.role.desc(), User.created_at.desc()), page)

    @classmethod
    def count_active_admins(cls) -> int:
        """启用状态的系统管理员数量：用于「最后一个管理员不可停用/降级」保护。"""
        return User.query.filter_by(role=ROLE_ADMIN, status="active").count()


class CategoryRepository(BaseRepository):
    model = Category

    @classmethod
    def active(cls):
        return Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.id).all()

    @classmethod
    def top_level(cls):
        return (Category.query.filter_by(is_active=True, parent_id=None)
                .order_by(Category.sort_order, Category.id).all())


class FoundItemRepository(BaseRepository):
    model = FoundItem

    @classmethod
    def by_code(cls, code: str):
        return FoundItem.query.filter_by(code=code).first()

    @classmethod
    def search(cls, *, keyword=None, category_id=None, zone=None, status=None,
               date_from=None, date_to=None, page=1, order="new"):
        """分类检索 + 模糊搜索（标题/描述/地点/关键词/单号）。"""
        q = FoundItem.query
        if keyword:
            like = f"%{keyword}%"
            q = q.filter(db.or_(FoundItem.title.like(like),
                                FoundItem.description.like(like),
                                FoundItem.found_place.like(like),
                                FoundItem.keywords.like(like),
                                FoundItem.code.like(like)))
        if category_id:
            q = q.filter(FoundItem.category_id == category_id)
        if zone:
            q = q.filter(FoundItem.found_zone == zone)
        if status:
            q = q.filter(FoundItem.status == status)
        if date_from:
            q = q.filter(FoundItem.found_time >= date_from)
        if date_to:
            q = q.filter(FoundItem.found_time <= date_to)
        q = q.order_by(FoundItem.found_time.desc() if order == "new" else FoundItem.view_count.desc())
        return paginate(q, page)

    @classmethod
    def candidates_for_matching(cls):
        """参与匹配的候选：仅未认领与待确认。"""
        return (FoundItem.query
                .filter(FoundItem.status.in_([ItemState.UNCLAIMED, ItemState.PENDING_CONFIRM]))
                .order_by(FoundItem.found_time.desc()).all())

    @classmethod
    def by_founder(cls, user_id: int, page: int = 1):
        return paginate(FoundItem.query.filter_by(founder_id=user_id)
                        .order_by(FoundItem.created_at.desc()), page)


class LostItemRepository(BaseRepository):
    model = LostItem

    @classmethod
    def by_code(cls, code: str):
        return LostItem.query.filter_by(code=code).first()

    @classmethod
    def search(cls, *, keyword=None, category_id=None, zone=None, status=None,
               date_from=None, date_to=None, page=1, order="new"):
        q = LostItem.query
        if keyword:
            like = f"%{keyword}%"
            q = q.filter(db.or_(LostItem.title.like(like),
                                LostItem.description.like(like),
                                LostItem.lost_place.like(like),
                                LostItem.keywords.like(like),
                                LostItem.code.like(like)))
        if category_id:
            q = q.filter(LostItem.category_id == category_id)
        if zone:
            q = q.filter(LostItem.lost_zone == zone)
        if status:
            q = q.filter(LostItem.status == status)
        if date_from:
            q = q.filter(LostItem.lost_time >= date_from)
        if date_to:
            q = q.filter(LostItem.lost_time <= date_to)
        q = q.order_by(LostItem.lost_time.desc() if order == "new" else LostItem.view_count.desc())
        return paginate(q, page)

    @classmethod
    def candidates_for_matching(cls):
        return (LostItem.query
                .filter(LostItem.status.in_([ItemState.UNCLAIMED, ItemState.PENDING_CONFIRM]))
                .order_by(LostItem.lost_time.desc()).all())

    @classmethod
    def by_owner(cls, user_id: int, page: int = 1):
        return paginate(LostItem.query.filter_by(owner_id=user_id)
                        .order_by(LostItem.created_at.desc()), page)


class ClaimRepository(BaseRepository):
    model = Claim

    @classmethod
    def by_no(cls, no: str):
        return Claim.query.filter_by(claim_no=no).first()

    @classmethod
    def pending_for_item(cls, found_item_id: int):
        return Claim.query.filter_by(found_item_id=found_item_id, status=ClaimState.PENDING).all()

    @classmethod
    def by_claimant(cls, user_id: int, page: int = 1):
        return paginate(Claim.query.filter_by(claimant_id=user_id)
                        .order_by(Claim.created_at.desc()), page)

    @classmethod
    def inbox_for_handler(cls, user_id: int, page: int = 1):
        """待我审核：我发布的物品收到的申请；职工/管理员可见全部待审。"""
        q = (Claim.query.join(FoundItem, Claim.found_item_id == FoundItem.id)
             .filter(db.or_(FoundItem.founder_id == user_id, Claim.status == ClaimState.PENDING))
             .order_by(Claim.created_at.desc()))
        return paginate(q, page)

    @classmethod
    def all_pending(cls, page: int = 1):
        return paginate(Claim.query.filter_by(status=ClaimState.PENDING)
                        .order_by(Claim.created_at.desc()), page)


class MatchRepository(BaseRepository):
    model = MatchRecord

    @classmethod
    def pair(cls, found_id: int, lost_id: int):
        return MatchRecord.query.filter_by(found_item_id=found_id, lost_item_id=lost_id).first()

    @classmethod
    def top_for_lost(cls, lost_id: int, limit: int = 5):
        return (MatchRecord.query.filter_by(lost_item_id=lost_id)
                .order_by(MatchRecord.score.desc()).limit(limit).all())

    @classmethod
    def top_for_found(cls, found_id: int, limit: int = 5):
        return (MatchRecord.query.filter_by(found_item_id=found_id)
                .order_by(MatchRecord.score.desc()).limit(limit).all())

    @classmethod
    def upsert(cls, found_id: int, lost_id: int, score: float, detail: dict, level: str):
        """幂等写入：同 (拾获, 寻物) 对只保留一条，重复跑只更新分数。"""
        rec = cls.pair(found_id, lost_id)
        payload = json.dumps(detail, ensure_ascii=False)
        if rec is None:
            rec = MatchRecord(found_item_id=found_id, lost_item_id=lost_id,
                              score=score, detail=payload, level=level)
            db.session.add(rec)
        else:
            rec.score, rec.detail, rec.level = score, payload, level
        db.session.commit()
        return rec


class NotificationRepository(BaseRepository):
    model = Notification

    @classmethod
    def for_user(cls, user_id: int, page: int = 1, unread_only: bool = False):
        q = Notification.query.filter_by(user_id=user_id)
        if unread_only:
            q = q.filter_by(is_read=False)
        return paginate(q.order_by(Notification.created_at.desc()), page)

    @classmethod
    def unread_count(cls, user_id: int) -> int:
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()


class LogRepository(BaseRepository):
    model = OperationLog

    @classmethod
    def recent(cls, page: int = 1, action: str | None = None, user_id: int | None = None):
        q = OperationLog.query
        if action:
            q = q.filter(OperationLog.action == action)
        if user_id:
            q = q.filter(OperationLog.user_id == user_id)
        return paginate(q.order_by(OperationLog.created_at.desc()), page)

    @classmethod
    def trace(cls, target_type: str, target_id: int):
        """单条业务对象的全链路追溯。"""
        return (OperationLog.query.filter_by(target_type=target_type, target_id=target_id)
                .order_by(OperationLog.created_at.asc()).all())


class AttachmentRepository(BaseRepository):
    model = Attachment

    @classmethod
    def by_entity(cls, entity_type: str, entity_id: int):
        return Attachment.query.filter_by(entity_type=entity_type, entity_id=entity_id).all()


class LoginAttemptRepository(BaseRepository):
    model = LoginAttempt

    @classmethod
    def recent_fails(cls, username: str, since: datetime) -> int:
        return LoginAttempt.query.filter(
            LoginAttempt.username == username,
            LoginAttempt.success.is_(False),
            LoginAttempt.created_at >= since,
        ).count()

    @classmethod
    def clear(cls, username: str) -> None:
        LoginAttempt.query.filter_by(username=username).delete()
        db.session.commit()
