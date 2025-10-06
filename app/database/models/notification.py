# app/database/models/notification.py
from datetime import datetime
from app import db


class Notification(db.Model):
    """Model representing a user notification."""

    __tablename__ = "notification"

    # 🔑 Identificatore
    id = db.Column(db.Integer, primary_key=True)

    # Recipient user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    # Notification type (e.g., "participation_request", "new_post", "new_campaign")
    type = db.Column(db.String(50), nullable=False)

    # Message content
    message = db.Column(db.Text, nullable=False)

    # Optional target URL
    url = db.Column(db.String(255), nullable=True)

    # Read status
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Aggiunta relazione con Post
    post_id = db.Column(db.Integer, db.ForeignKey("post.id", name="fk_notification_post_id"), nullable=True)

    # relazione opzionale col post
    post = db.relationship("Post", backref="notifications")

    # Relationship with user
    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} type={self.type} read={self.is_read}>"

    def to_dict(self):
        """Return a dictionary representation of the notification."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "message": self.message,
            "url": self.url,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Useful indexes
db.Index("ix_notification_user_read", Notification.user_id, Notification.is_read)
db.Index("ix_notification_created_at", Notification.created_at)
