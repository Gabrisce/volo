# app/database/models/donation.py
from datetime import datetime
from app import db


class Donation(db.Model):
    """Model representing a donation linked to a campaign."""

    __tablename__ = "donation"

    id = db.Column(db.Integer, primary_key=True)

    # Linked volunteer (optional)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    user = db.relationship("User", backref=db.backref("donations", lazy=True))

    # Donor details
    full_name = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(150), nullable=False)

    # Donation info
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), nullable=False)  # e.g. "card"
    message = db.Column(db.Text, nullable=True)

    # Receipt PDF (optional)
    pdf_filename = db.Column(db.String(255), nullable=True)

    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Linked campaign
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False, index=True)
    campaign = db.relationship("Campaign", backref=db.backref("donations", lazy=True))

    def __repr__(self) -> str:
        return f"<Donation id={self.id} user_id={self.user_id} campaign_id={self.campaign_id} amount={self.amount}>"
