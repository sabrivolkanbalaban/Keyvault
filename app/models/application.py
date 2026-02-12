from app import db


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    # Basic Information
    name = db.Column(db.String(255), nullable=False, index=True)
    server_name = db.Column(db.String(255), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")
    description = db.Column(db.Text, nullable=True)

    # Technical Details
    operating_system = db.Column(db.String(100), nullable=True)
    platform = db.Column(db.String(50), nullable=True)
    database_type = db.Column(db.String(100), nullable=True)
    app_version = db.Column(db.String(100), nullable=True)
    deployment_type = db.Column(db.String(50), nullable=True)

    # Management
    responsible_person = db.Column(db.String(255), nullable=True)
    department = db.Column(db.String(200), nullable=True)
    maintenance_date = db.Column(db.Date, nullable=True)
    sla_level = db.Column(db.String(20), nullable=True)
    criticality = db.Column(db.String(30), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Ownership & Timestamps
    created_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    created_by = db.relationship("User", backref="created_applications")

    @property
    def status_badge_class(self):
        return "success" if self.status == "active" else "secondary"

    @property
    def criticality_badge_class(self):
        return {
            "Mission Critical": "danger",
            "Business Critical": "warning text-dark",
            "Business Operational": "info",
            "Administrative": "secondary",
        }.get(self.criticality, "secondary")

    @property
    def sla_badge_class(self):
        return {
            "Critical": "danger",
            "High": "warning text-dark",
            "Medium": "info",
            "Low": "secondary",
        }.get(self.sla_level, "secondary")

    def __repr__(self):
        return f"<Application {self.name}>"
