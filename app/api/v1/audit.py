from flask import jsonify, request
from flask_login import current_user, login_required

from app.api.v1 import api_v1_bp
from app.auth.decorators import admin_required
from app.models.audit_log import AuditLog


@api_v1_bp.route("/audit", methods=["GET"])
@login_required
@admin_required
def api_audit_logs():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    action = request.args.get("action")
    username = request.args.get("username", "").strip()

    query = AuditLog.query
    if action:
        query = query.filter(AuditLog.action == action)
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "success": True,
        "data": [
            {
                "id": log.id,
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address,
                "success": log.success,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


@api_v1_bp.route("/audit/my", methods=["GET"])
@login_required
def api_my_audit():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)

    pagination = (
        AuditLog.query.filter_by(user_id=current_user.id)
        .order_by(AuditLog.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "success": True,
        "data": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_name": log.resource_name,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })
