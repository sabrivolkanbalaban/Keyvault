from app import db


class SecretShare(db.Model):
    __tablename__ = "secret_shares"

    id = db.Column(db.Integer, primary_key=True)
    secret_id = db.Column(
        db.Integer,
        db.ForeignKey("secrets.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    group_id = db.Column(
        db.Integer, db.ForeignKey("groups.id"), nullable=True
    )
    permission = db.Column(db.String(20), default="read")
    shared_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )

    # Relationships
    secret = db.relationship("Secret", back_populates="shares")
    user = db.relationship("User", foreign_keys=[user_id], back_populates="shared_secrets")
    group = db.relationship("Group")
    shared_by = db.relationship("User", foreign_keys=[shared_by_id])

    __table_args__ = (
        db.CheckConstraint(
            "user_id IS NOT NULL OR group_id IS NOT NULL",
            name="share_target_check",
        ),
    )

    def __repr__(self):
        target = f"user={self.user_id}" if self.user_id else f"group={self.group_id}"
        return f"<SecretShare secret={self.secret_id} {target}>"
