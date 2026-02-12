from datetime import date

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
from app.models.application import Application
from app.services.application_service import (
    CRITICALITY_CHOICES,
    DEPLOYMENT_CHOICES,
    PLATFORM_CHOICES,
    SLA_CHOICES,
    STATUS_CHOICES,
    ApplicationService,
)

applications_bp = Blueprint(
    "applications", __name__, url_prefix="/applications"
)

_FORM_CHOICES = dict(
    platform_choices=PLATFORM_CHOICES,
    deployment_choices=DEPLOYMENT_CHOICES,
    sla_choices=SLA_CHOICES,
    criticality_choices=CRITICALITY_CHOICES,
    status_choices=STATUS_CHOICES,
)


@applications_bp.route("/")
@login_required
def list_applications():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ITEMS_PER_PAGE", 25)
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip() or None
    platform = request.args.get("platform", "").strip() or None

    pagination = ApplicationService.get_applications(
        q=q or None,
        status=status,
        platform=platform,
        page=page,
        per_page=per_page,
    )
    return render_template(
        "applications/list.html",
        applications=pagination.items,
        pagination=pagination,
        platform_choices=PLATFORM_CHOICES,
        status_choices=STATUS_CHOICES,
        current_status=status,
        current_platform=platform,
        search_query=q,
    )


@applications_bp.route("/<int:app_id>")
@login_required
def detail(app_id):
    app_record = db.session.get(Application, app_id)
    if not app_record:
        abort(404)
    return render_template("applications/detail.html", app=app_record)


@applications_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Application name is required.", "danger")
            return render_template(
                "applications/form.html", app=None, **_FORM_CHOICES
            )

        kwargs = _extract_form_data()
        kwargs["name"] = name
        app_record = ApplicationService.create_application(
            user=current_user, **kwargs
        )
        flash(f"Application '{app_record.name}' created successfully.", "success")
        return redirect(url_for("applications.detail", app_id=app_record.id))

    return render_template(
        "applications/form.html", app=None, **_FORM_CHOICES
    )


@applications_bp.route("/<int:app_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit(app_id):
    app_record = db.session.get(Application, app_id)
    if not app_record:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Application name is required.", "danger")
            return render_template(
                "applications/form.html", app=app_record, **_FORM_CHOICES
            )

        kwargs = _extract_form_data()
        kwargs["name"] = name
        ApplicationService.update_application(app_record, current_user, **kwargs)
        flash(f"Application '{app_record.name}' updated successfully.", "success")
        return redirect(url_for("applications.detail", app_id=app_record.id))

    return render_template(
        "applications/form.html", app=app_record, **_FORM_CHOICES
    )


@applications_bp.route("/<int:app_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(app_id):
    app_record = db.session.get(Application, app_id)
    if not app_record:
        abort(404)
    name = app_record.name
    ApplicationService.delete_application(app_record, current_user)
    flash(f"Application '{name}' deleted.", "success")
    return redirect(url_for("applications.list_applications"))


def _extract_form_data():
    def _parse_date(field_name):
        val = request.form.get(field_name, "").strip()
        if val:
            try:
                return date.fromisoformat(val)
            except ValueError:
                return None
        return None

    return {
        "server_name": request.form.get("server_name", "").strip() or None,
        "ip_address": request.form.get("ip_address", "").strip() or None,
        "port": request.form.get("port", type=int) or None,
        "url": request.form.get("url", "").strip() or None,
        "status": request.form.get("status", "active"),
        "description": request.form.get("description", "").strip() or None,
        "operating_system": request.form.get("operating_system", "").strip() or None,
        "platform": request.form.get("platform", "").strip() or None,
        "database_type": request.form.get("database_type", "").strip() or None,
        "app_version": request.form.get("app_version", "").strip() or None,
        "deployment_type": request.form.get("deployment_type", "").strip() or None,
        "responsible_person": request.form.get("responsible_person", "").strip() or None,
        "department": request.form.get("department", "").strip() or None,
        "maintenance_date": _parse_date("maintenance_date"),
        "sla_level": request.form.get("sla_level", "").strip() or None,
        "criticality": request.form.get("criticality", "").strip() or None,
        "notes": request.form.get("notes", "").strip() or None,
    }
