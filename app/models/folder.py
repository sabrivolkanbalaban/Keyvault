from app import db


class Folder(db.Model):
    __tablename__ = "folders"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    parent_id = db.Column(
        db.Integer, db.ForeignKey("folders.id"), nullable=True
    )
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    icon = db.Column(db.String(50), default="folder")
    color = db.Column(db.String(7), default="#6c757d")
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )

    # Relationships
    secrets = db.relationship("Secret", back_populates="folder")
    children = db.relationship(
        "Folder", backref=db.backref("parent", remote_side=[id])
    )
    owner = db.relationship("User")

    def __repr__(self):
        return f"<Folder {self.name}>"
