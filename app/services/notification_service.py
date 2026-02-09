from datetime import datetime, timedelta, timezone

from sqlalchemy import and_

from app.models.secret import Secret


class NotificationService:
    @staticmethod
    def get_expiring_secrets(days_threshold: int = 30) -> list:
        """Get secrets expiring within the threshold."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_threshold)
        return Secret.query.filter(
            and_(
                Secret.expires_at.isnot(None),
                Secret.expires_at <= cutoff,
                Secret.expires_at > now,
            )
        ).all()

    @staticmethod
    def get_expired_secrets() -> list:
        """Get already expired secrets."""
        now = datetime.now(timezone.utc)
        return Secret.query.filter(
            and_(
                Secret.expires_at.isnot(None),
                Secret.expires_at <= now,
            )
        ).all()

    @staticmethod
    def get_stale_passwords(days_threshold: int = 90) -> list:
        """Get secrets where password hasn't been changed within threshold."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        return Secret.query.filter(
            and_(
                Secret.encrypted_password.isnot(None),
                Secret.password_last_changed.isnot(None),
                Secret.password_last_changed < cutoff,
                Secret.rotation_interval_days.isnot(None),
            )
        ).all()
