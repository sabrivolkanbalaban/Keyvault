from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models.secret import Secret
from app.models.audit_log import AuditLog
from app.services.application_service import ApplicationService
from app.services.license_service import LicenseService
from app.services.notification_service import NotificationService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    # Counts
    if current_user.is_admin():
        total_secrets = Secret.query.count()
    else:
        total_secrets = Secret.query.filter_by(owner_id=current_user.id).count()

    from app.models.share import SecretShare

    shared_count = SecretShare.query.filter_by(user_id=current_user.id).count()

    # Expiring secrets
    expiring = NotificationService.get_expiring_secrets(days_threshold=30)
    if not current_user.is_admin():
        expiring = [s for s in expiring if s.owner_id == current_user.id]

    # Recent activity
    recent_logs = (
        AuditLog.query.filter_by(user_id=current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )

    # Recent secrets
    recent_secrets = (
        Secret.query.filter_by(owner_id=current_user.id)
        .order_by(Secret.created_at.desc())
        .limit(10)
        .all()
    )

    # License stats
    license_stats = LicenseService.get_dashboard_stats()

    # Application stats
    app_stats = ApplicationService.get_dashboard_stats()

    return render_template(
        "dashboard/index.html",
        total_secrets=total_secrets,
        shared_count=shared_count,
        expiring_secrets=expiring,
        recent_logs=recent_logs,
        recent_secrets=recent_secrets,
        license_stats=license_stats,
        app_stats=app_stats,
    )
