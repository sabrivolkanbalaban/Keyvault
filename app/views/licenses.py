from datetime import datetime
from decimal import Decimal, InvalidOperation

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
from app.models.license import License, LicenseAssignment
from app.services.license_service import LICENSE_TYPES, LicenseService

licenses_bp = Blueprint("licenses", __name__, url_prefix="/licenses")


@licenses_bp.route("/")
@login_required
def list_licenses():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ITEMS_PER_PAGE", 25)
    q = request.args.get("q", "").strip()
    license_type = request.args.get("license_type")
    status = request.args.get("status")

    pagination = LicenseService.get_licenses(
        q=q or None,
        license_type=license_type,
        status=status,
        page=page,
        per_page=per_page,
    )

    return render_template(
        "licenses/list.html",
        licenses=pagination.items,
        pagination=pagination,
        license_types=LICENSE_TYPES,
        current_type=license_type,
        current_status=status,
        search_query=q,
    )


@licenses_bp.route("/my")
@login_required
def my_licenses():
    assignments = LicenseService.get_user_licenses(
        current_user.username, current_user.full_name
    )
    return render_template(
        "licenses/my_licenses.html",
        assignments=assignments,
    )


@licenses_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Product name is required.", "danger")
            return render_template(
                "licenses/form.html", license=None, license_types=LICENSE_TYPES
            )

        kwargs = _extract_form_data()
        kwargs["name"] = name

        lic = LicenseService.create_license(user=current_user, **kwargs)
        flash(f"License '{lic.name}' created successfully.", "success")
        return redirect(url_for("licenses.detail", license_id=lic.id))

    return render_template(
        "licenses/form.html", license=None, license_types=LICENSE_TYPES
    )


@licenses_bp.route("/<int:license_id>")
@login_required
def detail(license_id):
    lic = db.session.get(License, license_id)
    if not lic:
        abort(404)

    active_assignments = [a for a in lic.assignments if a.is_active]
    inactive_assignments = [a for a in lic.assignments if not a.is_active]

    return render_template(
        "licenses/detail.html",
        license=lic,
        active_assignments=active_assignments,
        inactive_assignments=inactive_assignments,
    )


@licenses_bp.route("/<int:license_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit(license_id):
    lic = db.session.get(License, license_id)
    if not lic:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Product name is required.", "danger")
            return render_template(
                "licenses/form.html", license=lic, license_types=LICENSE_TYPES
            )

        kwargs = _extract_form_data()
        kwargs["name"] = name

        new_key = request.form.get("license_key", "").strip()
        if new_key:
            kwargs["license_key"] = new_key

        LicenseService.update_license(lic, current_user, **kwargs)
        flash(f"License '{lic.name}' updated successfully.", "success")
        return redirect(url_for("licenses.detail", license_id=lic.id))

    return render_template(
        "licenses/form.html", license=lic, license_types=LICENSE_TYPES
    )


@licenses_bp.route("/<int:license_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(license_id):
    lic = db.session.get(License, license_id)
    if not lic:
        abort(404)

    name = lic.name
    LicenseService.delete_license(lic, current_user)
    flash(f"License '{name}' deleted.", "success")
    return redirect(url_for("licenses.list_licenses"))


@licenses_bp.route("/<int:license_id>/assign", methods=["GET", "POST"])
@login_required
@admin_required
def assign(license_id):
    lic = db.session.get(License, license_id)
    if not lic:
        abort(404)

    if request.method == "POST":
        assigned_to = request.form.get("assigned_to", "").strip()
        if not assigned_to:
            flash("Please enter a user name.", "danger")
            return redirect(url_for("licenses.assign", license_id=license_id))

        notes = request.form.get("notes", "").strip() or None
        machine_name = request.form.get("machine_name", "").strip() or None

        assignment, error = LicenseService.assign_user(
            lic, assigned_to, current_user, notes=notes, machine_name=machine_name
        )
        if error:
            flash(error, "danger")
        else:
            flash(f"'{assigned_to}' assigned to license successfully.", "success")
        return redirect(url_for("licenses.detail", license_id=lic.id))

    return render_template(
        "licenses/assign.html",
        license=lic,
    )


@licenses_bp.route(
    "/<int:license_id>/unassign/<int:assignment_id>", methods=["POST"]
)
@login_required
@admin_required
def unassign(license_id, assignment_id):
    lic = db.session.get(License, license_id)
    if not lic:
        abort(404)

    assignment = db.session.get(LicenseAssignment, assignment_id)
    if assignment and assignment.license_id == lic.id and assignment.is_active:
        LicenseService.unassign_user(assignment, current_user)
        flash("User unassigned from license.", "success")

    return redirect(url_for("licenses.detail", license_id=lic.id))


def _extract_form_data():
    def _parse_date(field_name):
        val = request.form.get(field_name, "").strip()
        if val:
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                return None
        return None

    def _parse_decimal(field_name):
        val = request.form.get(field_name, "").strip()
        if val:
            try:
                return Decimal(val)
            except (ValueError, InvalidOperation):
                return None
        return None

    return {
        "vendor": request.form.get("vendor", "").strip() or None,
        "version": request.form.get("version", "").strip() or None,
        "description": request.form.get("description", "").strip() or None,
        "license_type": request.form.get("license_type", "perpetual"),
        "cost": _parse_decimal("cost"),
        "currency": request.form.get("currency", "USD").strip() or "USD",
        "purchase_order": request.form.get("purchase_order", "").strip() or None,
        "purchase_date": _parse_date("purchase_date"),
        "expiration_date": _parse_date("expiration_date"),
        "support_expiration_date": _parse_date("support_expiration_date"),
        "seat_count": request.form.get("seat_count", type=int) or None,
        "vendor_contact": request.form.get("vendor_contact", "").strip() or None,
        "support_plan": request.form.get("support_plan", "").strip() or None,
        "department": request.form.get("department", "").strip() or None,
        "notes": request.form.get("notes", "").strip() or None,
        "license_key": request.form.get("license_key", "").strip() or None,
        "is_active": request.form.get("is_active") == "on",
    }
