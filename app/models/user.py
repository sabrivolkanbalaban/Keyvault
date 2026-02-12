from datetime import datetime, timezone

from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    full_name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=True)
    department = db.Column(db.String(200), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    ad_domain = db.Column(db.String(255), nullable=True)
    ad_dn = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    secrets = db.relationship(
        "Secret", back_populates="owner", foreign_keys="Secret.owner_id"
    )
    shared_secrets = db.relationship(
        "SecretShare", back_populates="user", foreign_keys="SecretShare.user_id"
    )
    groups = db.relationship(
        "Group", secondary="user_groups", back_populates="members"
    )

    def is_locked(self):
        if self.locked_until:
            now = datetime.now(timezone.utc)
            locked = self.locked_until
            if locked.tzinfo is None:
                locked = locked.replace(tzinfo=timezone.utc)
            return locked > now
        return False

    def is_admin(self):
        return self.role == "admin"

    def is_readonly(self):
        return self.role == "readonly"

    def can_write(self):
        return self.role in ("admin", "user")

    def __repr__(self):
        return f"<User {self.username}>"
