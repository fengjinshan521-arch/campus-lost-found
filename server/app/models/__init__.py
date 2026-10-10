"""数据访问层（Model 层）统一出口。"""
from app.models.base import BaseModel
from app.models.category import Category
from app.models.claim import (
    CLAIM_TYPE_AGENT,
    CLAIM_TYPE_MATCH,
    CLAIM_TYPE_SELF,
    CLAIM_STATUS_LABELS,
    Claim,
)
from app.models.item import (
    ITEM_STATUS_LABELS,
    FoundItem,
    LostItem,
)
from app.models.match import (
    MATCH_CONFIRMED,
    MATCH_IGNORED,
    MATCH_NEW,
    MATCH_NOTIFIED,
    MatchRecord,
)
from app.models.system import (
    NOTIFY_CLAIM,
    NOTIFY_MATCH,
    NOTIFY_RESULT,
    NOTIFY_SYSTEM,
    Attachment,
    Notification,
    OperationLog,
    SystemSetting,
)
from app.models.user import (
    ROLE_ADMIN,
    ROLE_STAFF,
    ROLE_STUDENT,
    ROLES,
    STATUS_ACTIVE,
    STATUS_DISABLED,
    LoginAttempt,
    User,
)

__all__ = [
    "BaseModel",
    "User", "LoginAttempt",
    "ROLE_ADMIN", "ROLE_STAFF", "ROLE_STUDENT", "ROLES",
    "STATUS_ACTIVE", "STATUS_DISABLED",
    "Category",
    "FoundItem", "LostItem", "ITEM_STATUS_LABELS",
    "Claim", "CLAIM_STATUS_LABELS", "CLAIM_TYPE_SELF", "CLAIM_TYPE_AGENT", "CLAIM_TYPE_MATCH",
    "MatchRecord", "MATCH_NEW", "MATCH_NOTIFIED", "MATCH_IGNORED", "MATCH_CONFIRMED",
    "Notification", "NOTIFY_MATCH", "NOTIFY_CLAIM", "NOTIFY_RESULT", "NOTIFY_SYSTEM",
    "OperationLog", "Attachment", "SystemSetting",
]
