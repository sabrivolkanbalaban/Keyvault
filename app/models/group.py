from app import db

user_groups = db.Table(
    "user_groups",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id"),
        primary_key=True,
    ),
    db.Column(
        "group_id",
        db.Integer,
        db.ForeignKey("groups.id"),
        primary_key=True,
    ),
    db.Column("added_at", db.DateTime, server_default=db.func.now()),
)


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    ad_group_dn = db.Column(db.Text, nullable=True)
    is_ad_synced = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )

    members = db.relationship(
        "User", secondary=user_groups, back_populates="groups"
    )

    def __repr__(self):
        return f"<Group {self.name}>"
