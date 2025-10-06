# app/database/models/chat.py
from app import db


class Chat(db.Model):
    """Model representing a conversation between two users."""

    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)

    # Participants
    user1_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Creation timestamp
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("user1_id", "user2_id", name="_user_pair_uc"),
    )

    def __repr__(self) -> str:
        return f"<Chat id={self.id} users=({self.user1_id}, {self.user2_id})>"
