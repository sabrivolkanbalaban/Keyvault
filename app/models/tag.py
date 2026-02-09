from app import db

secret_tags = db.Table(
    "secret_tags",
    db.Column(
        "secret_id",
        db.Integer,
        db.ForeignKey("secrets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.Integer,
        db.ForeignKey("tags.id"),
        primary_key=True,
    ),
)


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    color = db.Column(db.String(7), default="#007bff")

    secrets = db.relationship(
        "Secret", secondary=secret_tags, back_populates="tags"
    )

    def __repr__(self):
        return f"<Tag {self.name}>"
