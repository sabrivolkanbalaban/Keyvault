from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app import db, limiter
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.ldap_service import LDAPService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _map_ad_groups_to_role(ad_groups: list, config) -> str | None:
    """Map AD group memberships to a local role."""
    admin_groups = [g.strip() for g in config.get("LDAP_ADMIN_GROUPS", []) if g.strip()]
    user_groups = [g.strip() for g in config.get("LDAP_USER_GROUPS", []) if g.strip()]
    readonly_groups = [g.strip() for g in config.get("LDAP_READONLY_GROUPS", []) if g.strip()]

    for group_dn in ad_groups:
        if group_dn in admin_groups:
            return "admin"

    for group_dn in ad_groups:
        if group_dn in user_groups:
            return "user"

    for group_dn in ad_groups:
        if group_dn in readonly_groups:
            return "readonly"

    return None


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("auth/login.html")

        # Check if account is locked
        user = User.query.filter_by(username=username).first()
        if user and user.is_locked():
            flash("Account is temporarily locked. Please try again later.", "danger")
            return render_template("auth/login.html")

        # Attempt LDAP authentication
        ad_user = None
        if current_app.debug and username == "admin" and password == "admin":
            # Dev mode bypass - auto-create admin user without LDAP
            ad_user = {
                "username": "admin",
                "email": "admin@company.local",
                "full_name": "Admin User",
                "display_name": "Admin",
                "department": "IT",
                "title": "System Administrator",
                "dn": "CN=admin,DC=company,DC=local",
                "groups": [],
            }
        else:
            try:
                ldap_svc = LDAPService(current_app.config)
                ad_user = ldap_svc.authenticate(username, password)
            except Exception:
                flash("Authentication service unavailable. Please try again later.", "danger")
                return render_template("auth/login.html")

        if ad_user is None:
            if user:
                user.failed_login_attempts += 1
                max_attempts = current_app.config.get("MAX_LOGIN_ATTEMPTS", 5)
                lockout_minutes = current_app.config.get("LOCKOUT_DURATION_MINUTES", 15)
                if user.failed_login_attempts >= max_attempts:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(
                        minutes=lockout_minutes
                    )
                db.session.commit()
            AuditService.log(
                "login_failed",
                username=username,
                ip=request.remote_addr,
                success=False,
            )
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")

        # Upsert user in local DB
        if not user:
            user = User(
                username=ad_user["username"],
                full_name=ad_user["full_name"],
                role="user",
            )
            db.session.add(user)

        # Sync AD attributes
        user.email = ad_user["email"]
        user.full_name = ad_user["full_name"]
        user.display_name = ad_user["display_name"]
        user.department = ad_user["department"]
        user.title = ad_user["title"]
        user.ad_dn = ad_user["dn"]
        user.ad_domain = current_app.config["LDAP_DOMAIN"]
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = request.remote_addr
        user.failed_login_attempts = 0
        user.locked_until = None

        # Map AD groups to roles
        role = _map_ad_groups_to_role(ad_user["groups"], current_app.config)
        if role:
            user.role = role
        elif current_app.debug and username == "admin":
            user.role = "admin"

        db.session.commit()
        login_user(user, remember=remember)
        AuditService.log(
            "login",
            user_id=user.id,
            username=user.username,
            ip=request.remote_addr,
        )

        next_page = request.args.get("next")
        if next_page and not next_page.startswith("/"):
            next_page = None
        return redirect(next_page or url_for("dashboard.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    AuditService.log(
        "logout",
        user_id=current_user.id,
        username=current_user.username,
    )
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
