from datetime import datetime

from flask import abort, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.api.v1 import api_v1_bp
from app.auth.decorators import write_required
from app.models.secret import Secret
from app.services.export_service import ExportService
from app.services.secret_service import SecretService


def _secret_to_dict(secret, include_sensitive=False):
    data = {
        "id": secret.id,
        "name": secret.name,
        "description": secret.description,
        "category": secret.category,
        "url_domain": secret.url_domain,
        "folder_id": secret.folder_id,
        "owner_id": secret.owner_id,
        "is_favorite": secret.is_favorite,
        "expires_at": secret.expires_at.isoformat() if secret.expires_at else None,
        "tags": [t.name for t in secret.tags],
        "created_at": secret.created_at.isoformat() if secret.created_at else None,
        "updated_at": secret.updated_at.isoformat() if secret.updated_at else None,
    }
    if include_sensitive:
        data.update({
            "username": secret.username,
            "password": secret.password,
            "url": secret.url,
            "notes": secret.notes,
            "api_key": secret.api_key,
        })
    return data


@api_v1_bp.route("/secrets", methods=["GET"])
@login_required
def api_list_secrets():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    category = request.args.get("category")
    folder_id = request.args.get("folder_id", type=int)
    q = request.args.get("q", "").strip() or None

    pagination = SecretService.get_accessible_secrets(
        user=current_user,
        folder_id=folder_id,
        category=category,
        q=q,
        page=page,
        per_page=per_page,
    )

    return jsonify({
        "success": True,
        "data": [_secret_to_dict(s) for s in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


@api_v1_bp.route("/secrets/<int:secret_id>", methods=["GET"])
@login_required
def api_get_secret(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if not SecretService.can_user_access(secret, current_user):
        abort(403)

    SecretService.log_view(secret, current_user)
    return jsonify({"success": True, "data": _secret_to_dict(secret, include_sensitive=True)})


@api_v1_bp.route("/secrets", methods=["POST"])
@login_required
@write_required
def api_create_secret():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"success": False, "message": "Name is required"}), 400

    expires_at = None
    if data.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(data["expires_at"])
        except ValueError:
            return jsonify({"success": False, "message": "Invalid expires_at format"}), 400

    secret = SecretService.create_secret(
        user=current_user,
        name=data["name"],
        category=data.get("category", "credential"),
        username=data.get("username"),
        password=data.get("password"),
        url=data.get("url"),
        notes=data.get("notes"),
        api_key=data.get("api_key"),
        folder_id=data.get("folder_id"),
        tags=data.get("tags"),
        expires_at=expires_at,
        rotation_interval_days=data.get("rotation_interval_days"),
    )

    return jsonify({"success": True, "data": _secret_to_dict(secret, include_sensitive=True)}), 201


@api_v1_bp.route("/secrets/<int:secret_id>", methods=["PUT"])
@login_required
@write_required
def api_update_secret(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if not SecretService.can_user_access(secret, current_user, require_write=True):
        abort(403)

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    kwargs = {}
    for field in ("name", "description", "category", "username", "password",
                   "url", "notes", "api_key", "folder_id", "tags",
                   "rotation_interval_days", "is_favorite"):
        if field in data:
            kwargs[field] = data[field]

    if "expires_at" in data:
        try:
            kwargs["expires_at"] = datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None
        except ValueError:
            return jsonify({"success": False, "message": "Invalid expires_at format"}), 400

    SecretService.update_secret(secret, **kwargs)
    return jsonify({"success": True, "data": _secret_to_dict(secret, include_sensitive=True)})


@api_v1_bp.route("/secrets/<int:secret_id>", methods=["DELETE"])
@login_required
@write_required
def api_delete_secret(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if secret.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    SecretService.delete_secret(secret, current_user)
    return jsonify({"success": True, "message": "Secret deleted"})


@api_v1_bp.route("/secrets/export", methods=["GET"])
@login_required
def api_export_secrets():
    fmt = request.args.get("format", "json")
    secrets = Secret.query.filter_by(owner_id=current_user.id).all()

    if fmt == "csv":
        content = ExportService.export_csv(secrets)
        return content, 200, {"Content-Type": "text/csv", "Content-Disposition": "attachment; filename=secrets.csv"}

    content = ExportService.export_json(secrets)
    return content, 200, {"Content-Type": "application/json", "Content-Disposition": "attachment; filename=secrets.json"}


@api_v1_bp.route("/secrets/import", methods=["POST"])
@login_required
@write_required
def api_import_secrets():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400

    fmt = data.get("format", "json")
    content = data.get("content", "")

    if fmt == "keepass_csv":
        created = ExportService.import_keepass_csv(content, current_user.id)
    else:
        created = ExportService.import_json(content, current_user.id)

    for secret in created:
        db.session.add(secret)
    db.session.commit()

    return jsonify({"success": True, "message": f"{len(created)} secrets imported"})
