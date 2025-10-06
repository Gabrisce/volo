# app/database/models/participation.py
from datetime import datetime
from app import db


class Participation(db.Model):
    """Model representing a volunteer's participation in an event."""

    __tablename__ = "participation"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    volunteer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False, index=True)

    # Participation status: "pending", "accepted", "rejected", "cancelled"
    status = db.Column(db.String(20), nullable=False, default="pending")

    # Tracking
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    volunteer = db.relationship("User", backref="participations", foreign_keys=[volunteer_id])
    event = db.relationship("Event", backref="participants", foreign_keys=[event_id])

    __table_args__ = (
        db.UniqueConstraint("volunteer_id", "event_id", name="uq_participation_unique"),
    )

    def __repr__(self) -> str:
        return f"<Participation id={self.id} volunteer_id={self.volunteer_id} event_id={self.event_id} status={self.status}>"
