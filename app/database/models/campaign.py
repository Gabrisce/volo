# app/database/models/campaigns.py
from datetime import datetime
from typing import Any, Dict, Optional
from app import db


class Campaign(db.Model):
    """Model representing a fundraising campaign created by an association."""

    __tablename__ = "campaign"

    id = db.Column(db.Integer, primary_key=True)

    # Main content
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal_amount = db.Column(db.String(255), nullable=True)

    # Duration and period
    duration = db.Column(db.String(20), nullable=False, default="temporary", index=True)  # "temporary" | "perennial"
    date = db.Column(db.DateTime, nullable=False, index=True)  # Start date
    end_date = db.Column(db.DateTime, nullable=True, index=True)  # End date (only for temporary)

    # Location (optional)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(255), nullable=True, index=True)

    # Optional image
    image_filename = db.Column(db.String(255), nullable=True)

    # Tracking
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True,
    )

    # Association relationship
    association_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    association = db.relationship("User", back_populates="campaigns")

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} title='{self.title}'>"

    def to_map_dict(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Serialize campaign for map or feed usage."""
        return {
            "id": self.id,
            "type": "campaign",
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration": self.duration,
            "goal_amount": self.goal_amount,
            "location": self.location,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "image_filename": self.image_filename,
            "association_id": self.association_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "url": url,
        }


# Useful composite indexes
db.Index("ix_campaign_duration_dates", Campaign.duration, Campaign.date, Campaign.end_date)
db.Index("ix_campaign_geo", Campaign.latitude, Campaign.longitude)
