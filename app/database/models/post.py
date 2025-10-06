# app/database/models/post.py
from datetime import datetime
from app import db

class Post(db.Model):
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    association_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    applause = db.relationship(
        "Applause",
        back_populates="post",          # 👈 cambiato da backref a back_populates
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Post id={self.id} title='{self.title}'>"
