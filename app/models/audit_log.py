from app import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    resource_name = db.Column(db.String(255), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False, index=True
    )

    # Relationships
    user = db.relationship("User")

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.username}>"
