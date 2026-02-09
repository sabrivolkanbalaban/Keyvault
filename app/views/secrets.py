from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
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
from app.models.secret import Secret
from app.models.share import SecretShare
from app.models.tag import Tag
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.secret_service import SecretService

secrets_bp = Blueprint("secrets", __name__, url_prefix="/secrets")

CATEGORIES = [
    ("credential", "Credential"),
    ("url", "URL / Bookmark"),
    ("api_key", "API Key"),
    ("certificate", "Certificate"),
    ("note", "Secure Note"),
    ("database", "Database"),
    ("ssh_key", "SSH Key"),
    ("other", "Other"),
]


@secrets_bp.route("/")
@login_required
def list_secrets():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ITEMS_PER_PAGE", 25)
    category = request.args.get("category")
    folder_id = request.args.get("folder_id", type=int)
    q = request.args.get("q", "").strip()
    favorites = request.args.get("favorites") == "true"
    shared = request.args.get("shared") == "true"

    pagination = SecretService.get_accessible_secrets(
        user=current_user,
        folder_id=folder_id,
        category=category,
        q=q or None,
        favorites_only=favorites,
        shared_only=shared,
        page=page,
        per_page=per_page,
    )

    folders = Folder.query.filter_by(owner_id=current_user.id).all()

    return render_template(
        "secrets/list.html",
        secrets=pagination.items,
        pagination=pagination,
        categories=CATEGORIES,
        folders=folders,
        current_category=category,
        current_folder_id=folder_id,
        search_query=q,
        favorites=favorites,
        shared=shared,
    )


@secrets_bp.route("/new", methods=["GET", "POST"])
@login_required
@write_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Name is required.", "danger")
            return render_template(
                "secrets/form.html",
                secret=None,
                categories=CATEGORIES,
                folders=Folder.query.filter_by(owner_id=current_user.id).all(),
            )

        tags_str = request.form.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

        expires_at = None
        expires_str = request.form.get("expires_at", "").strip()
        if expires_str:
            try:
                expires_at = datetime.fromisoformat(expires_str)
            except ValueError:
                pass

        rotation = request.form.get("rotation_interval_days", type=int)

        secret = SecretService.create_secret(
            user=current_user,
            name=name,
            category=request.form.get("category", "credential"),
            username=request.form.get("secret_username", "").strip() or None,
            password=request.form.get("secret_password", "") or None,
            url=request.form.get("url", "").strip() or None,
            notes=request.form.get("notes", "").strip() or None,
            api_key=request.form.get("api_key", "").strip() or None,
            folder_id=request.form.get("folder_id", type=int) or None,
            tags=tags,
            expires_at=expires_at,
            rotation_interval_days=rotation,
        )
        flash(f"Secret '{secret.name}' created successfully.", "success")
        return redirect(url_for("secrets.detail", secret_id=secret.id))

    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    return render_template(
        "secrets/form.html",
        secret=None,
        categories=CATEGORIES,
        folders=folders,
    )


@secrets_bp.route("/<int:secret_id>")
@login_required
def detail(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if not SecretService.can_user_access(secret, current_user):
        abort(403)

    SecretService.log_view(secret, current_user)

    shares = SecretShare.query.filter_by(secret_id=secret.id).all()

    return render_template(
        "secrets/detail.html",
        secret=secret,
        shares=shares,
        is_owner=secret.owner_id == current_user.id,
    )


@secrets_bp.route("/<int:secret_id>/edit", methods=["GET", "POST"])
@login_required
@write_required
def edit(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if not SecretService.can_user_access(secret, current_user, require_write=True):
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Name is required.", "danger")
            return render_template(
                "secrets/form.html",
                secret=secret,
                categories=CATEGORIES,
                folders=Folder.query.filter_by(owner_id=current_user.id).all(),
            )

        tags_str = request.form.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        expires_at = None
        expires_str = request.form.get("expires_at", "").strip()
        if expires_str:
            try:
                expires_at = datetime.fromisoformat(expires_str)
            except ValueError:
                pass

        kwargs = {
            "name": name,
            "category": request.form.get("category", "credential"),
            "description": request.form.get("description", "").strip() or None,
            "username": request.form.get("secret_username", "").strip() or None,
            "url": request.form.get("url", "").strip() or None,
            "notes": request.form.get("notes", "").strip() or None,
            "api_key": request.form.get("api_key", "").strip() or None,
            "folder_id": request.form.get("folder_id", type=int) or None,
            "tags": tags,
            "expires_at": expires_at,
            "rotation_interval_days": request.form.get(
                "rotation_interval_days", type=int
            ),
        }

        # Only update password if a new one is provided
        new_password = request.form.get("secret_password", "")
        if new_password:
            kwargs["password"] = new_password

        SecretService.update_secret(secret, **kwargs)
        flash(f"Secret '{secret.name}' updated successfully.", "success")
        return redirect(url_for("secrets.detail", secret_id=secret.id))

    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    return render_template(
        "secrets/form.html",
        secret=secret,
        categories=CATEGORIES,
        folders=folders,
    )


@secrets_bp.route("/<int:secret_id>/delete", methods=["POST"])
@login_required
@write_required
def delete(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if secret.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    name = secret.name
    SecretService.delete_secret(secret, current_user)
    flash(f"Secret '{name}' deleted.", "success")
    return redirect(url_for("secrets.list_secrets"))


@secrets_bp.route("/<int:secret_id>/toggle-favorite", methods=["POST"])
@login_required
def toggle_favorite(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if not SecretService.can_user_access(secret, current_user):
        abort(403)

    secret.is_favorite = not secret.is_favorite
    db.session.commit()
    return redirect(request.referrer or url_for("secrets.list_secrets"))


@secrets_bp.route("/<int:secret_id>/copy-password", methods=["POST"])
@login_required
def copy_password(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if not SecretService.can_user_access(secret, current_user):
        abort(403)

    SecretService.log_password_copy(secret, current_user)
    return {"success": True}


@secrets_bp.route("/<int:secret_id>/share", methods=["GET", "POST"])
@login_required
@write_required
def share(secret_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if secret.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        group_id = request.form.get("group_id", type=int)
        permission = request.form.get("permission", "read")

        if not user_id and not group_id:
            flash("Select a user or group to share with.", "danger")
            return redirect(url_for("secrets.share", secret_id=secret_id))

        share_entry = SecretShare(
            secret_id=secret.id,
            user_id=user_id,
            group_id=group_id,
            permission=permission,
            shared_by_id=current_user.id,
        )
        db.session.add(share_entry)
        db.session.commit()

        AuditService.log(
            action="secret_shared",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="secret",
            resource_id=secret.id,
            resource_name=secret.name,
            details=f"Shared with user_id={user_id} group_id={group_id} permission={permission}",
        )
        flash("Secret shared successfully.", "success")
        return redirect(url_for("secrets.detail", secret_id=secret.id))

    users = User.query.filter(User.id != current_user.id, User.is_active.is_(True)).all()
    from app.models.group import Group

    groups = Group.query.all()
    existing_shares = SecretShare.query.filter_by(secret_id=secret.id).all()

    return render_template(
        "secrets/share.html",
        secret=secret,
        users=users,
        groups=groups,
        existing_shares=existing_shares,
    )


@secrets_bp.route("/<int:secret_id>/unshare/<int:share_id>", methods=["POST"])
@login_required
@write_required
def unshare(secret_id, share_id):
    secret = db.session.get(Secret, secret_id)
    if not secret:
        abort(404)
    if secret.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    share_entry = db.session.get(SecretShare, share_id)
    if share_entry and share_entry.secret_id == secret.id:
        db.session.delete(share_entry)
        db.session.commit()
        AuditService.log(
            action="secret_unshared",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="secret",
            resource_id=secret.id,
            resource_name=secret.name,
        )
        flash("Share removed.", "success")

    return redirect(url_for("secrets.detail", secret_id=secret.id))
