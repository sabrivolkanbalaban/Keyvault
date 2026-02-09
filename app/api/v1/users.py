from flask import abort, current_app, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.api.v1 import api_v1_bp
from app.auth.decorators import admin_required
from app.models.user import User
from app.services.ldap_service import LDAPService


@api_v1_bp.route("/users", methods=["GET"])
@login_required
@admin_required
def api_list_users():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    q = request.args.get("q", "").strip()

    query = User.query
    if q:
        search = f"%{q}%"
        query = query.filter(
            User.username.ilike(search)
            | User.full_name.ilike(search)
            | User.email.ilike(search)
        )

    pagination = query.order_by(User.username).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "success": True,
        "data": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "department": u.department,
                "role": u.role,
                "is_active": u.is_active,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            }
            for u in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


@api_v1_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@login_required
@admin_required
def api_change_role(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    data = request.get_json()
    new_role = data.get("role") if data else None
    if new_role not in ("admin", "user", "readonly"):
        return jsonify({"success": False, "message": "Invalid role"}), 400

    user.role = new_role
    db.session.commit()
    return jsonify({"success": True, "message": f"Role changed to {new_role}"})


@api_v1_bp.route("/users/search-ad", methods=["GET"])
@login_required
@admin_required
def api_search_ad():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"success": False, "message": "Query too short"}), 400

    try:
        ldap_svc = LDAPService(current_app.config)
        results = ldap_svc.search_users(q)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    return jsonify({"success": True, "data": results})
