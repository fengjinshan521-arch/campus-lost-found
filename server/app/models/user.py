"""用户与角色（用户与权限管理模块）。"""
import hashlib
import hmac
import secrets
from datetime import UTC, datetime

from flask_login import UserMixin

from app.extensions import db, login_manager
from app.models.base import BaseModel

ROLE_STUDENT = "student"
ROLE_STAFF = "staff"
ROLE_ADMIN = "admin"
ROLES = {
    ROLE_STUDENT: "学生用户",
    ROLE_STAFF: "楼管/保卫处",
    ROLE_ADMIN: "系统管理员",
}

STATUS_ACTIVE = "active"
STATUS_DISABLED = "disabled"


class User(UserMixin, BaseModel):
    __tablename__ = "t_user"

    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    student_no = db.Column(db.String(32), unique=True, nullable=True, index=True)
    real_name = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    college = db.Column(db.String(64), nullable=True)

    password_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(32), nullable=False)

    role = db.Column(db.String(16), default=ROLE_STUDENT, nullable=False, index=True)
    status = db.Column(db.String(16), default=STATUS_ACTIVE, nullable=False)
    credit_score = db.Column(db.Integer, default=100, nullable=False)

    verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(64), nullable=True)

    # 找回密码：一次性重置令牌（默认通过邮件/短信下发，演示环境直接回传前端）
    reset_token = db.Column(db.String(64), nullable=True, index=True)
    reset_token_expire = db.Column(db.DateTime, nullable=True)

    found_items = db.relationship("FoundItem", backref="founder", lazy="dynamic",
                                  foreign_keys="FoundItem.founder_id")
    lost_items = db.relationship("LostItem", backref="owner", lazy="dynamic",
                                 foreign_keys="LostItem.owner_id")
    claims = db.relationship("Claim", backref="claimant", lazy="dynamic",
                             foreign_keys="Claim.claimant_id")

    # ---------- 密码：PBKDF2-HMAC-SHA256 + 每用户独立随机盐 ----------
    @staticmethod
    def _hash_password(password: str, salt: str, iterations: int = 120_000) -> str:
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return dk.hex()

    def set_password(self, password: str, iterations: int = 120_000) -> None:
        self.salt = secrets.token_hex(16)
        self.password_hash = self._hash_password(password, self.salt, iterations)

    def check_password(self, password: str, iterations: int = 120_000) -> bool:
        if not self.salt or not self.password_hash:
            return False
        candidate = self._hash_password(password, self.salt, iterations)
        return hmac.compare_digest(candidate, self.password_hash)

    # ---------- 角色与状态 ----------
    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def is_staff(self) -> bool:
        return self.role in (ROLE_STAFF, ROLE_ADMIN)

    @property
    def role_label(self) -> str:
        return ROLES.get(self.role, self.role)

    def touch_login(self, ip: str | None = None) -> None:
        self.last_login_at = datetime.now(UTC).replace(tzinfo=None)
        self.last_login_ip = ip


class LoginAttempt(BaseModel):
    """登录失败记录：防爆破锁定的数据支撑。"""
    __tablename__ = "t_login_attempt"

    username = db.Column(db.String(32), nullable=False, index=True)
    ip = db.Column(db.String(64), nullable=True)
    success = db.Column(db.Boolean, default=False, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    @property
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > datetime.now(UTC).replace(tzinfo=None))


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
