from flask import abort, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.api.v1 import api_v1_bp
from app.auth.decorators import write_required
from app.models.folder import Folder


@api_v1_bp.route("/folders", methods=["GET"])
@login_required
def api_list_folders():
    if current_user.is_admin():
        folders = Folder.query.filter_by(parent_id=None).all()
    else:
        folders = Folder.query.filter_by(
            owner_id=current_user.id, parent_id=None
        ).all()

    def folder_to_dict(f):
        return {
            "id": f.id,
            "name": f.name,
            "description": f.description,
            "icon": f.icon,
            "color": f.color,
            "secret_count": len(f.secrets),
            "children": [folder_to_dict(c) for c in f.children],
        }

    return jsonify({"success": True, "data": [folder_to_dict(f) for f in folders]})


@api_v1_bp.route("/folders", methods=["POST"])
@login_required
@write_required
def api_create_folder():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"success": False, "message": "Name is required"}), 400

    folder = Folder(
        name=data["name"],
        description=data.get("description"),
        parent_id=data.get("parent_id"),
        owner_id=current_user.id,
        icon=data.get("icon", "folder"),
        color=data.get("color", "#6c757d"),
    )
    db.session.add(folder)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {"id": folder.id, "name": folder.name},
    }), 201


@api_v1_bp.route("/folders/<int:folder_id>", methods=["DELETE"])
@login_required
@write_required
def api_delete_folder(folder_id):
    folder = db.session.get(Folder, folder_id)
    if not folder:
        abort(404)
    if folder.owner_id != current_user.id and not current_user.is_admin():
        abort(403)
    if folder.secrets:
        return jsonify({"success": False, "message": "Folder has secrets"}), 400

    db.session.delete(folder)
    db.session.commit()
    return jsonify({"success": True, "message": "Folder deleted"})
