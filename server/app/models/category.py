"""物品分类（自引用外键支持二级分类）。"""
from app.extensions import db
from app.models.base import BaseModel


class Category(BaseModel):
    __tablename__ = "t_category"

    name = db.Column(db.String(32), unique=True, nullable=False)
    code = db.Column(db.String(32), unique=True, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("t_category.id", ondelete="SET NULL"), nullable=True)
    icon = db.Column(db.String(64), default="Box")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    children = db.relationship(
        "Category", backref=db.backref("parent", remote_side="Category.id"), lazy="dynamic"
    )
    found_items = db.relationship("FoundItem", backref="category", lazy="dynamic")
    lost_items = db.relationship("LostItem", backref="category", lazy="dynamic")

    @property
    def full_name(self) -> str:
        return f"{self.parent.name} / {self.name}" if self.parent else self.name

    def to_dict(self, exclude: set | None = None) -> dict:
        data = super().to_dict(exclude)
        data["full_name"] = self.full_name
        return data

    def __repr__(self):
        return f"<Category {self.name}>"
