from flask import Blueprint, current_app, render_template, request
from flask_login import current_user, login_required

from app.auth.decorators import admin_required
from app.models.audit_log import AuditLog

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/")
@login_required
@admin_required
def logs():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ITEMS_PER_PAGE", 25)
    action_filter = request.args.get("action")
    user_filter = request.args.get("username", "").strip()

    query = AuditLog.query
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if user_filter:
        query = query.filter(AuditLog.username.ilike(f"%{user_filter}%"))

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    actions = [
        "login", "login_failed", "logout",
        "secret_created", "secret_viewed", "secret_updated", "secret_deleted",
        "secret_shared", "secret_unshared", "password_copied",
        "user_role_changed", "user_status_changed",
    ]

    return render_template(
        "audit/logs.html",
        logs=pagination.items,
        pagination=pagination,
        actions=actions,
        current_action=action_filter,
        username_filter=user_filter,
    )


@audit_bp.route("/my")
@login_required
def my_logs():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ITEMS_PER_PAGE", 25)

    pagination = (
        AuditLog.query.filter_by(user_id=current_user.id)
        .order_by(AuditLog.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "audit/my_logs.html",
        logs=pagination.items,
        pagination=pagination,
    )
