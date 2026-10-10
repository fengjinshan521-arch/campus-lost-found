"""模型基类：统一主键与时间戳。"""
from datetime import UTC, datetime

from app.extensions import db

_utcnow = lambda: datetime.now(UTC).replace(tzinfo=None)


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def save(self, commit: bool = True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit: bool = True):
        db.session.delete(self)
        if commit:
            db.session.commit()

    def to_dict(self, exclude: set | None = None) -> dict:
        exclude = exclude or set()
        data = {}
        for col in self.__table__.columns:
            if col.name in exclude:
                continue
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.strftime("%Y-%m-%d %H:%M:%S")
            data[col.name] = val
        return data
