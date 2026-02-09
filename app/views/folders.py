from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.auth.decorators import write_required
from app.models.folder import Folder

folders_bp = Blueprint("folders", __name__, url_prefix="/folders")


@folders_bp.route("/")
@login_required
def list_folders():
    if current_user.is_admin():
        folders = Folder.query.filter_by(parent_id=None).all()
    else:
        folders = Folder.query.filter_by(
            owner_id=current_user.id, parent_id=None
        ).all()
    return render_template("folders/list.html", folders=folders)


@folders_bp.route("/new", methods=["GET", "POST"])
@login_required
@write_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Folder name is required.", "danger")
            return redirect(url_for("folders.create"))

        folder = Folder(
            name=name,
            description=request.form.get("description", "").strip() or None,
            parent_id=request.form.get("parent_id", type=int) or None,
            owner_id=current_user.id,
            icon=request.form.get("icon", "folder"),
            color=request.form.get("color", "#6c757d"),
        )
        db.session.add(folder)
        db.session.commit()
        flash(f"Folder '{folder.name}' created.", "success")
        return redirect(url_for("folders.list_folders"))

    parent_folders = Folder.query.filter_by(owner_id=current_user.id).all()
    return render_template("folders/form.html", folder=None, parent_folders=parent_folders)


@folders_bp.route("/<int:folder_id>/edit", methods=["GET", "POST"])
@login_required
@write_required
def edit(folder_id):
    folder = db.session.get(Folder, folder_id)
    if not folder:
        abort(404)
    if folder.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Folder name is required.", "danger")
            return redirect(url_for("folders.edit", folder_id=folder_id))

        folder.name = name
        folder.description = request.form.get("description", "").strip() or None
        folder.parent_id = request.form.get("parent_id", type=int) or None
        folder.icon = request.form.get("icon", "folder")
        folder.color = request.form.get("color", "#6c757d")
        db.session.commit()
        flash(f"Folder '{folder.name}' updated.", "success")
        return redirect(url_for("folders.list_folders"))

    parent_folders = Folder.query.filter(
        Folder.owner_id == current_user.id, Folder.id != folder.id
    ).all()
    return render_template("folders/form.html", folder=folder, parent_folders=parent_folders)


@folders_bp.route("/<int:folder_id>/delete", methods=["POST"])
@login_required
@write_required
def delete(folder_id):
    folder = db.session.get(Folder, folder_id)
    if not folder:
        abort(404)
    if folder.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    if folder.secrets:
        flash("Cannot delete folder with secrets. Move or delete them first.", "danger")
        return redirect(url_for("folders.list_folders"))

    name = folder.name
    db.session.delete(folder)
    db.session.commit()
    flash(f"Folder '{name}' deleted.", "success")
    return redirect(url_for("folders.list_folders"))
