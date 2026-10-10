"""后台管理与数据统计、日志追溯模块。

挂载前缀：/api/v1/admin
"""
from __future__ import annotations

from flask import Blueprint, request
from flask_login import current_user

from app.blueprints import payload, user_public
from app.decorators import admin_required, staff_required
from app.extensions import db
from app.models import Category, User
from app.models.user import ROLES, ROLE_ADMIN, ROLE_STAFF
from app.repositories import LogRepository, UserRepository
from app.schemas import fail, ok, paginated
from app.services import auth_service, log_service, match_service, notify_service, stats_service

bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------- 数据统计


@bp.get("/stats")
@staff_required
def stats():
    """后台看板：概览 + 认领率 + 分类分布 + 14 日趋势 + 高发地点 + 处理时长 + 状态漏斗。"""
    return ok({
        "overview": stats_service.overview(),
        "claim_rate": stats_service.claim_rate(),
        "category_distribution": stats_service.category_distribution(),
        "trend": stats_service.trend(14),
        "hot_locations": stats_service.hot_locations(8),
        "avg_handle_hours": stats_service.avg_handle_hours(),
        "status_pipeline": stats_service.status_pipeline(),
        "active_users": stats_service.active_users(10),
    })


@bp.get("/stats/public")
def stats_public():
    """首页公开的简要统计（无需登录）。"""
    o = stats_service.overview()
    return ok({
        "found_total": o["found_total"],
        "lost_total": o["lost_total"],
        "found_claimed": o["found_claimed"],
        "claim_rate": stats_service.claim_rate()["rate_percent"],
        "hot_locations": stats_service.hot_locations(5),
    })


# ---------------------------------------------------------------- 用户管理


@bp.get("/users")
@admin_required
def users():
    page_obj = UserRepository.search(
        keyword=(request.args.get("kw") or "").strip() or None,
        role=(request.args.get("role") or "").strip() or None,
        status=(request.args.get("status") or "").strip() or None,
        page=request.args.get("page", 1, type=int) or 1,
    )
    return ok(paginated(page_obj, [user_public(u) for u in page_obj.items]))


@bp.post("/users/<int:user_id>/status")
@admin_required
def set_status(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return fail("用户不存在", status=404)
    data = payload()
    status = (data.get("status") or "").strip()
    auth_service.set_user_status(user, current_user, status)
    return ok({"user": user_public(user)}, msg="账号状态已更新")


@bp.post("/users/<int:user_id>/role")
@admin_required
def set_role(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return fail("用户不存在", status=404)
    auth_service.set_user_role(user, current_user, (payload().get("role") or "").strip())
    return ok({"user": user_public(user)}, msg="角色已更新")


# ---------------------------------------------------------------- 管理员管理


@bp.get("/admins")
@admin_required
def admins():
    """管理人员列表（楼管 + 系统管理员），与学生用户列表分离。"""
    page_obj = UserRepository.search_managers(
        keyword=(request.args.get("kw") or "").strip() or None,
        role=(request.args.get("role") or "").strip() or None,
        status=(request.args.get("status") or "").strip() or None,
        page=request.args.get("page", 1, type=int) or 1,
    )
    return ok(paginated(page_obj, [user_public(u) for u in page_obj.items], {
        "admin_count": User.query.filter_by(role=ROLE_ADMIN).count(),
        "staff_count": User.query.filter_by(role=ROLE_STAFF).count(),
        "disabled_count": User.query.filter(User.role.in_([ROLE_STAFF, ROLE_ADMIN]),
                                            User.status == "disabled").count(),
        "active_admin_count": UserRepository.count_active_admins(),
        "roles": [{"value": ROLE_STAFF, "label": ROLES[ROLE_STAFF]},
                  {"value": ROLE_ADMIN, "label": ROLES[ROLE_ADMIN]}],
    }))


@bp.post("/admins")
@admin_required
def admin_create():
    """新建管理账号：楼管或系统管理员。"""
    # 业务异常（账号重复、密码强度不足等）由全局 errorhandler 统一转 JSON
    user = auth_service.create_manager(payload(), current_user)
    return ok({"user": user_public(user)}, msg="管理账号已创建")


@bp.put("/admins/<int:user_id>")
@admin_required
def admin_update(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return fail("账号不存在", status=404)
    if user.role not in (ROLE_STAFF, ROLE_ADMIN):
        return fail("该账号不是管理人员，请到「用户管理」中操作", status=400)
    user = auth_service.update_manager(user, payload(), current_user)
    return ok({"user": user_public(user)}, msg="管理账号已更新")


@bp.post("/admins/<int:user_id>/password")
@admin_required
def admin_reset_password(user_id):
    """重置管理账号密码（不需要原密码，用于交接与找回）。"""
    user = db.session.get(User, user_id)
    if user is None:
        return fail("账号不存在", status=404)
    auth_service.reset_password(user, payload().get("password") or "", current_user)
    return ok(msg="密码已重置，请通知该账号持有人及时修改")


@bp.post("/admins/<int:user_id>/status")
@admin_required
def admin_set_status(user_id):
    """启用/停用管理账号。"""
    user = db.session.get(User, user_id)
    if user is None:
        return fail("账号不存在", status=404)
    data = payload()
    user = auth_service.update_manager(user, {"status": (data.get("status") or "").strip()},
                                       current_user)
    return ok({"user": user_public(user)}, msg="账号状态已更新")


# ---------------------------------------------------------------- 分类管理


@bp.get("/categories")
def categories():
    cats = Category.query.order_by(Category.sort_order, Category.id).all()
    return ok({"categories": [c.to_dict() for c in cats]})


@bp.post("/categories")
@admin_required
def category_create():
    data = payload()
    name = (data.get("name") or "").strip()
    if not name:
        return fail("分类名称不能为空")
    if Category.query.filter_by(name=name).first():
        return fail("该分类已存在")
    parent_id = data.get("parent_id")
    cat = Category(
        name=name,
        code=(data.get("code") or "").strip() or None,
        parent_id=int(parent_id) if parent_id else None,
        sort_order=int(data.get("sort_order") or 0),
        description=(data.get("description") or "").strip() or None,
    )
    db.session.add(cat)
    db.session.commit()
    log_service.record("category_create", current_user, "category", cat.id, {"name": name})
    return ok({"category": cat.to_dict()}, msg="分类已创建")


@bp.put("/categories/<int:cat_id>")
@admin_required
def category_update(cat_id):
    cat = db.session.get(Category, cat_id)
    if cat is None:
        return fail("分类不存在", status=404)
    data = payload()
    before = cat.name
    if "name" in data and data.get("name"):
        cat.name = data["name"].strip()
    if "sort_order" in data:
        cat.sort_order = int(data.get("sort_order") or 0)
    if "is_active" in data:
        cat.is_active = bool(data.get("is_active"))
    if "description" in data:
        cat.description = (data.get("description") or "").strip() or None
    db.session.commit()
    log_service.record("category_update", current_user, "category", cat.id,
                       {"before": before, "after": cat.name})
    return ok({"category": cat.to_dict()}, msg="分类已更新")


@bp.delete("/categories/<int:cat_id>")
@admin_required
def category_delete(cat_id):
    cat = db.session.get(Category, cat_id)
    if cat is None:
        return fail("分类不存在", status=404)
    cat.is_active = False     # 软删除：保留历史数据的可追溯性
    db.session.commit()
    log_service.record("category_disable", current_user, "category", cat.id, {"name": cat.name})
    return ok(msg="分类已停用")


# ---------------------------------------------------------------- 日志追溯


@bp.get("/logs")
@admin_required
def logs():
    page_obj = LogRepository.recent(
        page=request.args.get("page", 1, type=int) or 1,
        action=(request.args.get("action") or "").strip() or None,
        user_id=request.args.get("user_id", type=int),
    )
    return ok(paginated(page_obj, [
        {
            "id": log.id,
            "action": log.action,
            "username": log.username,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "detail": log.detail,
            "ip": log.ip,
            "result": log.result,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for log in page_obj.items
    ]))


@bp.get("/logs/trace")
@admin_required
def logs_trace():
    """按 业务对象类型 + ID 拉取完整时间线，实现全流程可追溯。"""
    target_type = (request.args.get("target_type") or "").strip()
    target_id = request.args.get("target_id", type=int)
    if not target_type or not target_id:
        return fail("请提供 target_type 与 target_id")
    logs = LogRepository.trace(target_type, target_id)
    return ok({
        "target_type": target_type,
        "target_id": target_id,
        "timeline": [
            {
                "action": log.action,
                "username": log.username,
                "detail": log.detail,
                "ip": log.ip,
                "result": log.result,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for log in logs
        ],
    })


# ---------------------------------------------------------------- 运维动作


@bp.post("/match/run")
@staff_required
def run_match():
    """全量重算匹配（可挂定时任务或后台按钮触发）。"""
    result = match_service.run_full_matching(push_notify=True)
    log_service.record("match_run", current_user, None, None, result)
    return ok(result, msg=f"全量匹配完成：新增 {result['created']} 条，更新 {result['updated']} 条")


@bp.post("/notify/broadcast")
@admin_required
def broadcast():
    """系统公告广播给全体用户。"""
    data = payload()
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title:
        return fail("公告标题不能为空")
    count = notify_service.notify_broadcast([u.id for u in User.query.all()], title, content)
    log_service.record("notify_broadcast", current_user, None, None, {"count": count})
    return ok({"count": count}, msg=f"已广播给 {count} 位用户")
