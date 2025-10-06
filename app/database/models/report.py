# app/database/models/report.py
from datetime import datetime
from app import db


class Report(db.Model):
    """Model representing a report created by a volunteer."""

    __tablename__ = "report"

    id = db.Column(db.Integer, primary_key=True)

    # Main content
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Location
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Optional image
    image_filename = db.Column(db.String(255), nullable=True)

    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with user (author of the report)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<Report id={self.id} title='{self.title}'>"
