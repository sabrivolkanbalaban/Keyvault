from datetime import datetime, timedelta, timezone

from app import db


class License(db.Model):
    __tablename__ = "licenses"

    id = db.Column(db.Integer, primary_key=True)

    # Core identification
    name = db.Column(db.String(255), nullable=False, index=True)
    vendor = db.Column(db.String(255), nullable=True)
    version = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # License key (encrypted)
    encrypted_license_key = db.Column(db.Text, nullable=True)

    # Classification
    license_type = db.Column(db.String(50), nullable=False, default="perpetual")

    # Financial
    cost = db.Column(db.Numeric(12, 2), nullable=True)
    currency = db.Column(db.String(3), nullable=True, default="USD")
    purchase_order = db.Column(db.String(100), nullable=True)

    # Dates
    purchase_date = db.Column(db.DateTime, nullable=True)
    expiration_date = db.Column(db.DateTime, nullable=True, index=True)
    support_expiration_date = db.Column(db.DateTime, nullable=True)

    # Seats
    seat_count = db.Column(db.Integer, nullable=True)

    # Contact / support
    vendor_contact = db.Column(db.String(255), nullable=True)
    support_plan = db.Column(db.String(100), nullable=True)

    # Organization
    department = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Ownership
    created_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    # Encryption metadata
    encryption_version = db.Column(db.Integer, default=1)

    # Timestamps
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    created_by = db.relationship("User", backref="created_licenses")
    assignments = db.relationship(
        "LicenseAssignment",
        back_populates="license",
        cascade="all, delete-orphan",
    )

    # --- Encrypted property accessor for license_key ---

    @property
    def license_key(self):
        if self.encrypted_license_key:
            from app.services.encryption_service import EncryptionService

            return EncryptionService.decrypt(self.encrypted_license_key)
        return None

    @license_key.setter
    def license_key(self, value):
        from app.services.encryption_service import EncryptionService

        self.encrypted_license_key = (
            EncryptionService.encrypt(value) if value else None
        )

    # --- Computed properties ---

    @property
    def used_seats(self):
        return len([a for a in self.assignments if a.is_active])

    @property
    def available_seats(self):
        if self.seat_count is None:
            return None
        return max(0, self.seat_count - self.used_seats)

    @property
    def utilization_percent(self):
        if self.seat_count is None or self.seat_count == 0:
            return None
        return round((self.used_seats / self.seat_count) * 100, 1)

    @property
    def is_expired(self):
        if self.expiration_date:
            return self.expiration_date <= datetime.now(timezone.utc)
        return False

    @property
    def is_expiring_soon(self):
        if self.expiration_date and not self.is_expired:
            cutoff = datetime.now(timezone.utc) + timedelta(days=30)
            return self.expiration_date <= cutoff
        return False

    @property
    def status_label(self):
        if not self.is_active:
            return "inactive"
        if self.is_expired:
            return "expired"
        if self.is_expiring_soon:
            return "expiring_soon"
        return "active"

    def __repr__(self):
        return f"<License {self.name}>"


class LicenseAssignment(db.Model):
    __tablename__ = "license_assignments"

    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(
        db.Integer,
        db.ForeignKey("licenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Free-text user identification
    assigned_to = db.Column(db.String(255), nullable=False)

    # Assignment metadata
    assigned_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    assigned_date = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
    unassigned_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(500), nullable=True)
    machine_name = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )

    # Relationships
    license = db.relationship("License", back_populates="assignments")
    assigned_by = db.relationship("User", foreign_keys=[assigned_by_id])

    def __repr__(self):
        return f"<LicenseAssignment license={self.license_id} assigned_to={self.assigned_to}>"
