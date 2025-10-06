# app/database/models/applause.py
from app import db
from datetime import datetime

class Applause(db.Model):
    __tablename__ = "applause"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Relations
    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Uniqueness: one user can applaud a post only once
    __table_args__ = (
        db.UniqueConstraint("post_id", "user_id", name="uq_post_user_applause"),
    )

    # Relationships
    user = db.relationship("User", back_populates="applause")
    post = db.relationship("Post", back_populates="applause")
