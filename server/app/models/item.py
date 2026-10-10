"""失物（寻物启事）与拾获（招领信息）两张核心业务表。"""
import json
from datetime import datetime

from app.extensions import db
from app.models.base import BaseModel
from app.services.state_machine import ItemState

STATUS_UNCLAIMED = ItemState.UNCLAIMED
STATUS_PENDING = ItemState.PENDING_CONFIRM
STATUS_CLAIMED = ItemState.CLAIMED
STATUS_ARCHIVED = ItemState.ARCHIVED
STATUS_CANCELLED = ItemState.CANCELLED

ITEM_STATUS_LABELS = {
    STATUS_UNCLAIMED: "未认领",
    STATUS_PENDING: "待确认",
    STATUS_CLAIMED: "已认领",
    STATUS_ARCHIVED: "已归档",
    STATUS_CANCELLED: "已撤销",
}


def _load_json_array(raw: str | None) -> list:
    try:
        data = json.loads(raw or "[]")
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


class FoundItem(BaseModel):
    """拾获登记：捡到物品并上交/发布招领。"""

    __tablename__ = "t_found_item"
    __table_args__ = (
        db.Index("idx_found_status_time", "status", "found_time"),
        db.Index("idx_found_cat_status", "category_id", "status"),
    )

    code = db.Column(db.String(32), unique=True, nullable=False, index=True)  # LF-2026-0001
    founder_id = db.Column(db.Integer, db.ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("t_category.id", ondelete="RESTRICT"), nullable=False)

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    features = db.Column(db.Text, nullable=True)         # JSON 数组 ["黑色","iPhone13"]
    keywords = db.Column(db.String(255), nullable=True)  # 空格分隔的检索关键词

    found_place = db.Column(db.String(128), nullable=False)
    found_zone = db.Column(db.String(32), nullable=True, index=True)
    found_time = db.Column(db.DateTime, nullable=False, index=True)
    storage_place = db.Column(db.String(128), nullable=True)  # 保管点，如"保卫处3号柜"

    images = db.Column(db.Text, nullable=True)           # JSON 数组 ["/static/uploads/..."]
    is_sensitive = db.Column(db.Boolean, default=False, nullable=False)

    status = db.Column(db.String(20), default=STATUS_UNCLAIMED, nullable=False, index=True)
    view_count = db.Column(db.Integer, default=0, nullable=False)

    claimed_by = db.Column(db.Integer, db.ForeignKey("t_user.id", ondelete="SET NULL"), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    claims = db.relationship("Claim", backref="found_item", lazy="dynamic",
                             foreign_keys="Claim.found_item_id")
    matches = db.relationship("MatchRecord", backref="found_item", lazy="dynamic",
                              foreign_keys="MatchRecord.found_item_id")

    @property
    def status_label(self) -> str:
        return ITEM_STATUS_LABELS.get(self.status, self.status)

    @property
    def feature_list(self) -> list:
        return _load_json_array(self.features)

    @property
    def image_list(self) -> list:
        return _load_json_array(self.images)

    def to_dict(self, exclude: set | None = None) -> dict:
        data = super().to_dict(exclude)
        data["status_label"] = self.status_label
        data["feature_list"] = self.feature_list
        data["image_list"] = self.image_list
        return data


class LostItem(BaseModel):
    """寻物启事：失主发布的丢失信息。"""

    __tablename__ = "t_lost_item"
    __table_args__ = (
        db.Index("idx_lost_status_time", "status", "lost_time"),
        db.Index("idx_lost_cat_status", "category_id", "status"),
    )

    code = db.Column(db.String(32), unique=True, nullable=False, index=True)  # XS-2026-0001
    owner_id = db.Column(db.Integer, db.ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("t_category.id", ondelete="RESTRICT"), nullable=False)

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    features = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(255), nullable=True)

    lost_place = db.Column(db.String(128), nullable=False)
    lost_zone = db.Column(db.String(32), nullable=True, index=True)
    lost_time = db.Column(db.DateTime, nullable=False, index=True)

    images = db.Column(db.Text, nullable=True)
    reward = db.Column(db.String(100), nullable=True)
    is_urgent = db.Column(db.Boolean, default=False, nullable=False)

    status = db.Column(db.String(20), default=STATUS_UNCLAIMED, nullable=False, index=True)
    view_count = db.Column(db.Integer, default=0, nullable=False)

    matched_found_id = db.Column(
        db.Integer, db.ForeignKey("t_found_item.id", ondelete="SET NULL"), nullable=True
    )
    archived_at = db.Column(db.DateTime, nullable=True)

    matches = db.relationship("MatchRecord", backref="lost_item", lazy="dynamic",
                              foreign_keys="MatchRecord.lost_item_id")

    @property
    def status_label(self) -> str:
        return ITEM_STATUS_LABELS.get(self.status, self.status)

    @property
    def feature_list(self) -> list:
        return _load_json_array(self.features)

    @property
    def image_list(self) -> list:
        return _load_json_array(self.images)

    def days_from(self, other_time: datetime) -> float:
        return abs((self.lost_time - other_time).total_seconds()) / 86400.0

    def to_dict(self, exclude: set | None = None) -> dict:
        data = super().to_dict(exclude)
        data["status_label"] = self.status_label
        data["feature_list"] = self.feature_list
        data["image_list"] = self.image_list
        return data
