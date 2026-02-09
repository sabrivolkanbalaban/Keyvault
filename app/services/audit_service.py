from flask import request

from app import db
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log(
        action: str,
        user_id: int = None,
        username: str = None,
        resource_type: str = None,
        resource_id: int = None,
        resource_name: str = None,
        details: str = None,
        ip: str = None,
        success: bool = True,
    ):
        """Create an audit log entry. Designed to never throw."""
        try:
            log_entry = AuditLog(
                user_id=user_id,
                username=username or "anonymous",
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                details=details,
                ip_address=ip or _get_remote_addr(),
                user_agent=_get_user_agent(),
                success=success,
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception:
            db.session.rollback()


def _get_remote_addr():
    try:
        return request.remote_addr
    except RuntimeError:
        return None


def _get_user_agent():
    try:
        return request.headers.get("User-Agent")
    except RuntimeError:
        return None
