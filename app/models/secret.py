from datetime import datetime, timezone

from app import db


class Secret(db.Model):
    __tablename__ = "secrets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, default="credential")

    # Encrypted fields (stored as Fernet-encrypted base64 strings)
    encrypted_username = db.Column(db.Text, nullable=True)
    encrypted_password = db.Column(db.Text, nullable=True)
    encrypted_url = db.Column(db.Text, nullable=True)
    encrypted_notes = db.Column(db.Text, nullable=True)
    encrypted_api_key = db.Column(db.Text, nullable=True)
    encrypted_extra_data = db.Column(db.Text, nullable=True)

    # Metadata (not encrypted - needed for search/filter)
    url_domain = db.Column(db.String(255), nullable=True, index=True)

    # Organization
    folder_id = db.Column(db.Integer, db.ForeignKey("folders.id"), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Lifecycle
    is_favorite = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    password_last_changed = db.Column(db.DateTime, nullable=True)
    rotation_interval_days = db.Column(db.Integer, nullable=True)

    # Encryption metadata
    encryption_version = db.Column(db.Integer, default=1)

    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    owner = db.relationship("User", back_populates="secrets")
    folder = db.relationship("Folder", back_populates="secrets")
    shares = db.relationship(
        "SecretShare", back_populates="secret", cascade="all, delete-orphan"
    )
    tags = db.relationship("Tag", secondary="secret_tags", back_populates="secrets")

    # --- Encrypted property accessors ---

    @property
    def username(self):
        if self.encrypted_username:
            from app.services.encryption_service import EncryptionService

            return EncryptionService.decrypt(self.encrypted_username)
        return None

    @username.setter
    def username(self, value):
        from app.services.encryption_service import EncryptionService

        self.encrypted_username = EncryptionService.encrypt(value) if value else None

    @property
    def password(self):
        if self.encrypted_password:
            from app.services.encryption_service import EncryptionService

            return EncryptionService.decrypt(self.encrypted_password)
        return None

    @password.setter
    def password(self, value):
        from app.services.encryption_service import EncryptionService

        self.encrypted_password = EncryptionService.encrypt(value) if value else None
        if value:
            self.password_last_changed = datetime.now(timezone.utc)

    @property
    def url(self):
        if self.encrypted_url:
            from app.services.encryption_service import EncryptionService

            return EncryptionService.decrypt(self.encrypted_url)
        return None

    @url.setter
    def url(self, value):
        from app.services.encryption_service import EncryptionService

        self.encrypted_url = EncryptionService.encrypt(value) if value else None
        if value:
            from urllib.parse import urlparse

            try:
                parsed = urlparse(value)
                self.url_domain = parsed.netloc or parsed.path
            except Exception:
                self.url_domain = None

    @property
    def notes(self):
        if self.encrypted_notes:
            from app.services.encryption_service import EncryptionService

            return EncryptionService.decrypt(self.encrypted_notes)
        return None

    @notes.setter
    def notes(self, value):
        from app.services.encryption_service import EncryptionService

        self.encrypted_notes = EncryptionService.encrypt(value) if value else None

    @property
    def api_key(self):
        if self.encrypted_api_key:
            from app.services.encryption_service import EncryptionService

            return EncryptionService.decrypt(self.encrypted_api_key)
        return None

    @api_key.setter
    def api_key(self, value):
        from app.services.encryption_service import EncryptionService

        self.encrypted_api_key = EncryptionService.encrypt(value) if value else None

    @property
    def extra_data(self):
        if self.encrypted_extra_data:
            from app.services.encryption_service import EncryptionService
            import json

            return json.loads(EncryptionService.decrypt(self.encrypted_extra_data))
        return None

    @extra_data.setter
    def extra_data(self, value):
        from app.services.encryption_service import EncryptionService
        import json

        if value:
            self.encrypted_extra_data = EncryptionService.encrypt(json.dumps(value))
        else:
            self.encrypted_extra_data = None

    def __repr__(self):
        return f"<Secret {self.name}>"
