from datetime import datetime
from app import db


class Event(db.Model):
    """Model representing an event created by an association."""

    __tablename__ = "event"

    id = db.Column(db.Integer, primary_key=True)

    # Main details
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Date and location
    date = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(255), nullable=False)

    # Optional image
    image_filename = db.Column(db.String(255), nullable=True)

    # Optional coordinates
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Tracking
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True,
    )

    # Taxonomy and filters
    duration = db.Column(db.String(20), nullable=False, default="temporary", index=True)
    skills = db.Column(db.Text, nullable=False, default="[]")
    activity = db.Column(db.String(50), nullable=True, index=True)
    type = db.Column(db.String(20), nullable=False, default="event", index=True)

    # Capacity (None = unlimited)
    capacity_max = db.Column(db.Integer, nullable=True)

    # Association relationship
    association_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    association = db.relationship("User", back_populates="events")

    # Participation relationship
    participants = db.relationship(
        "Participation",
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    @property
    def is_limited(self) -> bool:
        """Return True if event has a participant limit."""
        return self.capacity_max is not None

    def accepted_count(self) -> int:
        """Count accepted participations for this event."""
        from app.database.models.participation import Participation
        return Participation.query.filter_by(event_id=self.id, status="accepted").count()

    def seats_left(self) -> int | None:
        """Return available seats, or None if unlimited."""
        if not self.is_limited:
            return None
        return max(self.capacity_max - self.accepted_count(), 0)

    def is_full(self) -> bool:
        """Return True if event reached maximum capacity."""
        return self.is_limited and self.seats_left() == 0

    @property
    def related_campaigns(self):
        """Return active fundraising campaigns of the same association."""
        from app.database.models.campaign import Campaign
        now = datetime.utcnow()
        return (
            Campaign.query.filter(
                Campaign.association_id == self.association_id,
                (Campaign.end_date.is_(None)) | (Campaign.end_date >= now),
            )
            .order_by(Campaign.created_at.desc())
            .limit(3)
            .all()
        )

    def __repr__(self) -> str:
        d = self.date.strftime("%Y-%m-%d %H:%M") if self.date else "N/A"
        return f"<Event id={self.id} title='{self.title}' date={d}>"


# Useful composite indexes
db.Index("ix_event_geo", Event.latitude, Event.longitude)
db.Index("ix_event_duration_date", Event.duration, Event.date)
