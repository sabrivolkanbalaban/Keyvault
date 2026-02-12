from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.auth.decorators import admin_required
from app.services.audit_service import AuditService
from app.services.oracle_service import OracleService

oracle_admin_bp = Blueprint("oracle_admin", __name__, url_prefix="/admin/oracle")


def _get_oracle_service():
    return OracleService(current_app.config)


@oracle_admin_bp.route("/")
@login_required
@admin_required
def index():
    """Main page: user list + privilege viewer."""
    selected_user = request.args.get("user", "").strip().upper()
    search_query = request.args.get("q", "").strip()

    try:
        svc = _get_oracle_service()
        oracle_users = svc.get_users()
    except Exception as e:
        flash(f"Oracle connection error: {e}", "danger")
        oracle_users = []

    if search_query:
        oracle_users = [
            u for u in oracle_users
            if search_query.upper() in u["username"]
        ]

    privileges = []
    if selected_user:
        try:
            svc = _get_oracle_service()
            privileges = svc.get_user_privileges(selected_user)
        except Exception as e:
            flash(f"Error fetching privileges: {e}", "danger")

    return render_template(
        "admin/oracle/privileges.html",
        oracle_users=oracle_users,
        selected_user=selected_user,
        privileges=privileges,
        search_query=search_query,
    )


@oracle_admin_bp.route("/schemas")
@login_required
@admin_required
def schemas():
    """Return schemas list as JSON (for AJAX)."""
    try:
        svc = _get_oracle_service()
        schema_list = svc.get_schemas()
        return jsonify({"success": True, "schemas": schema_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@oracle_admin_bp.route("/objects/<schema>")
@login_required
@admin_required
def objects(schema):
    """Return tables and views for a schema as JSON (for AJAX)."""
    try:
        svc = _get_oracle_service()
        object_list = svc.get_objects(schema)
        return jsonify({"success": True, "objects": object_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@oracle_admin_bp.route("/grant", methods=["POST"])
@login_required
@admin_required
def grant():
    """Grant privilege to a user."""
    grantee = request.form.get("grantee", "").strip().upper()
    schema = request.form.get("schema", "").strip().upper()
    object_name = request.form.get("object_name", "").strip().upper()
    privileges = request.form.getlist("privileges")

    if not grantee or not schema or not object_name or not privileges:
        flash("All fields are required.", "danger")
        return redirect(url_for("oracle_admin.index", user=grantee))

    svc = _get_oracle_service()
    errors = []
    granted = []

    for priv in privileges:
        result = svc.grant_privilege(grantee, priv, schema, object_name)
        if result["success"]:
            granted.append(priv)
        else:
            errors.append(f"{priv}: {result['error']}")

    if granted:
        priv_str = ", ".join(granted)
        AuditService.log(
            action="oracle_grant",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="oracle_privilege",
            resource_name=f"{schema}.{object_name}",
            details=f"GRANT {priv_str} ON {schema}.{object_name} TO {grantee}",
        )
        flash(
            f"Granted {priv_str} on {schema}.{object_name} to {grantee}.",
            "success",
        )

    for err in errors:
        flash(f"Grant error - {err}", "danger")

    return redirect(url_for("oracle_admin.index", user=grantee))


@oracle_admin_bp.route("/revoke", methods=["POST"])
@login_required
@admin_required
def revoke():
    """Revoke privilege from a user."""
    grantee = request.form.get("grantee", "").strip().upper()
    schema = request.form.get("schema", "").strip().upper()
    object_name = request.form.get("object_name", "").strip().upper()
    privilege = request.form.get("privilege", "").strip().upper()

    if not grantee or not schema or not object_name or not privilege:
        flash("Missing parameters for revoke.", "danger")
        return redirect(url_for("oracle_admin.index", user=grantee))

    svc = _get_oracle_service()
    result = svc.revoke_privilege(grantee, privilege, schema, object_name)

    if result["success"]:
        AuditService.log(
            action="oracle_revoke",
            user_id=current_user.id,
            username=current_user.username,
            resource_type="oracle_privilege",
            resource_name=f"{schema}.{object_name}",
            details=f"REVOKE {privilege} ON {schema}.{object_name} FROM {grantee}",
        )
        flash(
            f"Revoked {privilege} on {schema}.{object_name} from {grantee}.",
            "success",
        )
    else:
        flash(f"Revoke error: {result['error']}", "danger")

    return redirect(url_for("oracle_admin.index", user=grantee))
