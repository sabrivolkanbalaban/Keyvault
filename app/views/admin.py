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
from app.auth.decorators import admin_required
from app.models.group import Group
from app.models.user import User
from app.services.audit_service import AuditService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ITEMS_PER_PAGE", 25)
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
    return render_template(
        "admin/users.html", users=pagination.items, pagination=pagination, search_query=q
    )


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def change_role(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot change your own role.", "danger")
        return redirect(url_for("admin.users"))

    new_role = request.form.get("role")
    if new_role not in ("admin", "user", "readonly"):
        flash("Invalid role.", "danger")
        return redirect(url_for("admin.users"))

    old_role = user.role
    user.role = new_role
    db.session.commit()

    AuditService.log(
        action="user_role_changed",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=user.id,
        resource_name=user.username,
        details=f"Role changed from {old_role} to {new_role}",
    )
    flash(f"User '{user.username}' role changed to {new_role}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot deactivate yourself.", "danger")
        return redirect(url_for("admin.users"))

    user.is_active = not user.is_active
    db.session.commit()

    status = "activated" if user.is_active else "deactivated"
    AuditService.log(
        action="user_status_changed",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=user.id,
        resource_name=user.username,
        details=f"User {status}",
    )
    flash(f"User '{user.username}' {status}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        full_name = request.form.get("full_name", "").strip()
        if not username or not full_name:
            flash("Username and full name are required.", "danger")
            return render_template("admin/user_form.html", user=None)

        if User.query.filter_by(username=username).first():
            flash(f"User '{username}' already exists.", "danger")
            return render_template("admin/user_form.html", user=None)

        user = User(
            username=username,
            full_name=full_name,
            email=request.form.get("email", "").strip() or None,
            department=request.form.get("department", "").strip() or None,
            title=request.form.get("title", "").strip() or None,
            role=request.form.get("role", "user"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        AuditService.log(
            action="user_created",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="user",
            resource_id=user.id,
            resource_name=user.username,
            details=f"Created with role={user.role}",
        )
        flash(f"User '{user.username}' created. They can now log in via Active Directory.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/user_form.html", user=None)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        if not full_name:
            flash("Full name is required.", "danger")
            return render_template("admin/user_form.html", user=user)

        user.full_name = full_name
        user.email = request.form.get("email", "").strip() or None
        user.department = request.form.get("department", "").strip() or None
        user.title = request.form.get("title", "").strip() or None

        if user.id != current_user.id:
            user.role = request.form.get("role", user.role)

        db.session.commit()

        AuditService.log(
            action="user_updated",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="user",
            resource_id=user.id,
            resource_name=user.username,
        )
        flash(f"User '{user.username}' updated.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/user_form.html", user=user)


@admin_bp.route("/groups")
@login_required
@admin_required
def groups():
    all_groups = Group.query.order_by(Group.name).all()
    return render_template("admin/groups.html", groups=all_groups)


@admin_bp.route("/groups/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_group():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Group name is required.", "danger")
            return redirect(url_for("admin.create_group"))

        group = Group(
            name=name,
            description=request.form.get("description", "").strip() or None,
        )
        db.session.add(group)
        db.session.commit()
        flash(f"Group '{group.name}' created.", "success")
        return redirect(url_for("admin.groups"))

    return render_template("admin/group_form.html", group=None)


@admin_bp.route("/groups/<int:group_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_group(group_id):
    group = db.session.get(Group, group_id)
    if not group:
        abort(404)
    name = group.name
    db.session.delete(group)
    db.session.commit()
    flash(f"Group '{name}' deleted.", "success")
    return redirect(url_for("admin.groups"))
