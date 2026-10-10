"""公共接口：健康检查、字典元数据、CSRF Token、图片上传。

挂载前缀：/api/v1
"""
from __future__ import annotations

from flask import Blueprint, current_app, request
from flask_login import current_user
from flask_wtf.csrf import generate_csrf

from app.blueprints import user_public
from app.decorators import login_required_json
from app.extensions import db
from app.models import Attachment, Category
from app.models.claim import CLAIM_STATUS_LABELS
from app.models.item import ITEM_STATUS_LABELS
from app.models.user import ROLES
from app.schemas import fail, ok
from app.utils import save_upload

bp = Blueprint("main", __name__)


@bp.after_app_request
def inject_csrf_token(resp):
    """把 CSRF Token 写入响应头，前端 Axios 拦截后自动回传 X-CSRFToken。"""
    try:
        resp.headers.setdefault("X-CSRFToken", generate_csrf())
    except Exception:  # 生成失败不能影响正常响应
        pass
    return resp


@bp.get("/health")
def health():
    return ok({
        "status": "up",
        "service": "campus-lost-found",
        "debug": bool(current_app.config.get("DEBUG")),
        "threshold": current_app.config["MATCH_THRESHOLD"],
    })


@bp.get("/meta")
def meta():
    """前端下拉框用的字典数据：分类树、校园分区、状态标签、角色。"""
    cats = Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.id).all()
    tree = [
        {
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "children": [{"id": ch.id, "name": ch.name} for ch in cats if ch.parent_id == c.id],
        }
        for c in cats
        if c.parent_id is None
    ]
    return ok({
        "categories": tree,
        "zones": list(current_app.config["CAMPUS_ZONES"].keys()),
        "item_status": ITEM_STATUS_LABELS,
        "claim_status": CLAIM_STATUS_LABELS,
        "roles": ROLES,
    })


@bp.get("/csrf-token")
def csrf_token():
    """供前端首次请求时换取 CSRF Token（也可直接读任意响应头 X-CSRFToken）。"""
    return ok({"csrf_token": generate_csrf()})


@bp.get("/me")
def me():
    """当前登录用户；未登录返回 user=None，前端据此渲染顶栏。"""
    if not current_user.is_authenticated:
        return ok({"user": None})
    return ok({"user": user_public(current_user, full=True)})


@bp.post("/upload")
@login_required_json
def upload():
    """图片上传：扩展名白名单 + 魔数校验 + 随机重命名 + sha256 留痕。

    表单字段：file（必填）、entity_type、entity_id、subdir
    """
    file = request.files.get("file")
    if file is None or not file.filename:
        return fail("未选择文件")
    # 前端 UploadImages 组件传的是 entity_type；兼容显式 subdir，二者都缺时归入 misc
    subdir = (request.form.get("subdir") or request.form.get("entity_type") or "misc").strip()
    try:
        rel_url, original_name, size, checksum = save_upload(file, subdir=subdir)
    except ValueError as exc:
        return fail(str(exc))

    entity_id = request.form.get("entity_id", type=int)
    db.session.add(Attachment(
        entity_type=(request.form.get("entity_type") or "misc"),
        entity_id=entity_id,
        uploader_id=current_user.id,
        original_name=original_name,
        saved_name=rel_url.rsplit("/", 1)[-1],
        rel_path=rel_url,
        size=size,
        checksum=checksum,
    ))
    db.session.commit()
    return ok({"url": rel_url, "name": original_name, "size": size}, msg="上传成功")
