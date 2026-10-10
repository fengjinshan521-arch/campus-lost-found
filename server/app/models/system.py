"""系统支撑表：通知、操作日志、附件、系统参数。"""
from datetime import UTC, datetime

from app.extensions import db
from app.models.base import BaseModel

NOTIFY_MATCH = "match"
NOTIFY_CLAIM = "claim"
NOTIFY_RESULT = "result"
NOTIFY_SYSTEM = "system"


class Notification(BaseModel):
    __tablename__ = "t_notification"
    __table_args__ = (db.Index("idx_notify_user_read", "user_id", "is_read"),)

    user_id = db.Column(db.Integer, db.ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.String(20), default=NOTIFY_SYSTEM, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=True)
    related_type = db.Column(db.String(32), nullable=True)   # found_item / lost_item / claim
    related_id = db.Column(db.Integer, nullable=True)
    link = db.Column(db.String(255), nullable=True)          # 前端路由，如 /items/found/12
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))

    def mark_read(self, commit: bool = True):
        self.is_read = True
        self.read_at = datetime.now(UTC).replace(tzinfo=None)
        if commit:
            db.session.commit()
        return self


class OperationLog(BaseModel):
    """操作日志：全流程追溯的唯一事实来源。"""
    __tablename__ = "t_operation_log"
    __table_args__ = (db.Index("idx_log_target", "target_type", "target_id"),)

    user_id = db.Column(db.Integer, db.ForeignKey("t_user.id", ondelete="SET NULL"), nullable=True)
    username = db.Column(db.String(32), nullable=True)      # 冗余保存，用户注销后仍可追溯
    action = db.Column(db.String(64), nullable=False, index=True)
    target_type = db.Column(db.String(32), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    detail = db.Column(db.Text, nullable=True)              # JSON：变更前后值等
    ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    result = db.Column(db.String(16), default="success", nullable=False)  # success / fail

    user = db.relationship("User", backref=db.backref("operation_logs", lazy="dynamic"))


class Attachment(BaseModel):
    """上传附件留痕：原始名、存储名、大小、sha256 校验和。"""
    __tablename__ = "t_attachment"

    entity_type = db.Column(db.String(32), nullable=False)  # found_item / lost_item / claim
    entity_id = db.Column(db.Integer, nullable=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("t_user.id", ondelete="SET NULL"), nullable=True)
    original_name = db.Column(db.String(255), nullable=False)
    saved_name = db.Column(db.String(255), nullable=False, unique=True)
    rel_path = db.Column(db.String(255), nullable=False)    # 对外可访问 URL
    mime = db.Column(db.String(64), nullable=True)
    size = db.Column(db.Integer, default=0, nullable=False)
    checksum = db.Column(db.String(64), nullable=True)

    uploader = db.relationship("User", backref=db.backref("attachments", lazy="dynamic"))


class SystemSetting(BaseModel):
    """系统参数（如匹配权重后台调参）。"""
    __tablename__ = "t_system_setting"

    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    remark = db.Column(db.String(200), nullable=True)
