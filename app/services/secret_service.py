from datetime import datetime, timezone

from sqlalchemy import or_

from app import db
from app.models.secret import Secret
from app.models.share import SecretShare
from app.models.tag import Tag
from app.services.audit_service import AuditService


class SecretService:
    @staticmethod
    def get_accessible_secrets(user, folder_id=None, category=None, q=None,
                               favorites_only=False, shared_only=False,
                               page=1, per_page=25):
        """Get secrets the user can access (own + shared)."""
        # Base query: user's own secrets
        own_query = Secret.query.filter(Secret.owner_id == user.id)

        # Shared secrets
        shared_query = Secret.query.join(SecretShare).filter(
            or_(
                SecretShare.user_id == user.id,
                SecretShare.group_id.in_([g.id for g in user.groups]),
            ),
            or_(
                SecretShare.expires_at.is_(None),
                SecretShare.expires_at > datetime.now(timezone.utc),
            ),
        )

        if shared_only:
            query = shared_query
        elif user.is_admin():
            query = Secret.query
        else:
            query = own_query.union(shared_query)

        # Apply filters
        if folder_id is not None:
            query = query.filter(Secret.folder_id == folder_id)
        if category:
            query = query.filter(Secret.category == category)
        if favorites_only:
            query = query.filter(Secret.is_favorite.is_(True))
        if q:
            search = f"%{q}%"
            query = query.filter(
                or_(
                    Secret.name.ilike(search),
                    Secret.description.ilike(search),
                    Secret.url_domain.ilike(search),
                )
            )

        return query.order_by(Secret.updated_at.desc().nullsfirst(), Secret.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def create_secret(user, name, category, username=None, password=None,
                      url=None, notes=None, api_key=None, extra_data=None,
                      folder_id=None, tags=None, expires_at=None,
                      rotation_interval_days=None):
        """Create a new secret."""
        secret = Secret(
            name=name,
            category=category,
            owner_id=user.id,
            folder_id=folder_id,
            expires_at=expires_at,
            rotation_interval_days=rotation_interval_days,
        )
        secret.username = username
        secret.password = password
        secret.url = url
        secret.notes = notes
        secret.api_key = api_key
        secret.extra_data = extra_data

        if tags:
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name.strip()).first()
                if not tag:
                    tag = Tag(name=tag_name.strip())
                    db.session.add(tag)
                secret.tags.append(tag)

        db.session.add(secret)
        db.session.commit()

        AuditService.log(
            action="secret_created",
            user_id=user.id,
            username=user.username,
            resource_type="secret",
            resource_id=secret.id,
            resource_name=secret.name,
        )

        return secret

    @staticmethod
    def update_secret(secret, **kwargs):
        """Update a secret's fields."""
        for field in ("name", "description", "category", "folder_id",
                      "expires_at", "rotation_interval_days", "is_favorite"):
            if field in kwargs:
                setattr(secret, field, kwargs[field])

        for field in ("username", "password", "url", "notes", "api_key", "extra_data"):
            if field in kwargs:
                setattr(secret, field, kwargs[field])

        if "tags" in kwargs:
            secret.tags.clear()
            for tag_name in kwargs["tags"]:
                tag = Tag.query.filter_by(name=tag_name.strip()).first()
                if not tag:
                    tag = Tag(name=tag_name.strip())
                    db.session.add(tag)
                secret.tags.append(tag)

        db.session.commit()

        AuditService.log(
            action="secret_updated",
            user_id=secret.owner_id,
            username=secret.owner.username,
            resource_type="secret",
            resource_id=secret.id,
            resource_name=secret.name,
        )

        return secret

    @staticmethod
    def delete_secret(secret, user):
        """Delete a secret."""
        AuditService.log(
            action="secret_deleted",
            user_id=user.id,
            username=user.username,
            resource_type="secret",
            resource_id=secret.id,
            resource_name=secret.name,
        )
        db.session.delete(secret)
        db.session.commit()

    @staticmethod
    def log_view(secret, user):
        """Log that a user viewed a secret."""
        AuditService.log(
            action="secret_viewed",
            user_id=user.id,
            username=user.username,
            resource_type="secret",
            resource_id=secret.id,
            resource_name=secret.name,
        )

    @staticmethod
    def log_password_copy(secret, user):
        """Log that a user copied a password."""
        AuditService.log(
            action="password_copied",
            user_id=user.id,
            username=user.username,
            resource_type="secret",
            resource_id=secret.id,
            resource_name=secret.name,
        )

    @staticmethod
    def can_user_access(secret, user, require_write=False):
        """Check if user can access this secret."""
        if user.is_admin():
            return True
        if secret.owner_id == user.id:
            return True

        share = SecretShare.query.filter(
            SecretShare.secret_id == secret.id,
            or_(
                SecretShare.user_id == user.id,
                SecretShare.group_id.in_([g.id for g in user.groups]),
            ),
            or_(
                SecretShare.expires_at.is_(None),
                SecretShare.expires_at > datetime.now(timezone.utc),
            ),
        ).first()

        if not share:
            return False
        if require_write and share.permission != "write":
            return False
        return True
