"""匹配推荐记录：让"为什么推荐它"可解释、可追溯。"""
import json

from app.extensions import db
from app.models.base import BaseModel

MATCH_NEW = "new"
MATCH_NOTIFIED = "notified"
MATCH_IGNORED = "ignored"
MATCH_CONFIRMED = "confirmed"


class MatchRecord(BaseModel):
    __tablename__ = "t_match_record"
    __table_args__ = (
        db.UniqueConstraint("found_item_id", "lost_item_id", name="uq_match_pair"),
        db.Index("idx_match_score", "score"),
    )

    found_item_id = db.Column(
        db.Integer, db.ForeignKey("t_found_item.id", ondelete="CASCADE"), nullable=False
    )
    lost_item_id = db.Column(
        db.Integer, db.ForeignKey("t_lost_item.id", ondelete="CASCADE"), nullable=False
    )

    score = db.Column(db.Float, default=0.0, nullable=False)      # 综合得分 0~1
    detail = db.Column(db.Text, nullable=True)                    # JSON：各因子得分明细
    level = db.Column(db.String(16), default="low", nullable=True)  # high / medium / low
    status = db.Column(db.String(16), default=MATCH_NEW, nullable=False)
    notified_at = db.Column(db.DateTime, nullable=True)

    def detail_dict(self) -> dict:
        try:
            data = json.loads(self.detail or "{}")
            return data if isinstance(data, dict) else {}
        except (ValueError, TypeError):
            return {}

    def to_dict(self, exclude: set | None = None) -> dict:
        data = super().to_dict(exclude)
        data["detail"] = self.detail_dict()
        return data
