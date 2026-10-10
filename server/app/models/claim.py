"""认领记录：承载 待确认 → 已认领 → 已归档 的状态流转与操作留痕。"""
import json
from datetime import datetime

from app.extensions import db
from app.models.base import BaseModel
from app.services.state_machine import ClaimState

CLAIM_STATUS_LABELS = {
    ClaimState.PENDING: "待确认",
    ClaimState.APPROVED: "已认领",
    ClaimState.REJECTED: "已驳回",
    ClaimState.CANCELLED: "已取消",
    ClaimState.ARCHIVED: "已归档",
}

CLAIM_TYPE_SELF = "self"      # 本人认领
CLAIM_TYPE_AGENT = "agent"    # 代领
CLAIM_TYPE_MATCH = "match"    # 经系统匹配推荐后发起


class Claim(BaseModel):
    __tablename__ = "t_claim"
    __table_args__ = (
        db.Index("idx_claim_status", "status"),
        db.Index("idx_claim_item", "found_item_id", "status"),
    )

    claim_no = db.Column(db.String(32), unique=True, nullable=False, index=True)  # RQ-2026-0001
    found_item_id = db.Column(
        db.Integer, db.ForeignKey("t_found_item.id", ondelete="CASCADE"), nullable=False
    )
    lost_item_id = db.Column(
        db.Integer, db.ForeignKey("t_lost_item.id", ondelete="SET NULL"), nullable=True
    )
    claimant_id = db.Column(db.Integer, db.ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False)

    claim_type = db.Column(db.String(16), default=CLAIM_TYPE_SELF, nullable=False)
    status = db.Column(db.String(20), default=ClaimState.PENDING, nullable=False)

    reason = db.Column(db.Text, nullable=True)          # 认领理由 / 凭证描述
    evidence = db.Column(db.Text, nullable=True)        # JSON 数组：凭证图片
    contact = db.Column(db.String(64), nullable=True)   # 本次认领的临时联系方式

    handler_id = db.Column(db.Integer, db.ForeignKey("t_user.id", ondelete="SET NULL"), nullable=True)
    handle_comment = db.Column(db.Text, nullable=True)
    handled_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    handler = db.relationship("User", foreign_keys=[handler_id])

    @property
    def status_label(self) -> str:
        return CLAIM_STATUS_LABELS.get(self.status, self.status)

    @property
    def evidence_list(self) -> list:
        try:
            data = json.loads(self.evidence or "[]")
            return data if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    def is_open(self) -> bool:
        return self.status == ClaimState.PENDING

    def to_dict(self, exclude: set | None = None) -> dict:
        data = super().to_dict(exclude)
        data["status_label"] = self.status_label
        data["evidence_list"] = self.evidence_list
        return data
