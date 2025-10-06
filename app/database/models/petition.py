# app/database/models/petition.py
from app import db
from datetime import datetime


class Petition(db.Model):
    __tablename__ = "petitions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)

    # 👇 Associazione con il volontario che crea la petizione
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    signatures = db.relationship("PetitionSignature", back_populates="petition", cascade="all, delete-orphan")
    supports = db.relationship("PetitionSupport", back_populates="petition", cascade="all, delete-orphan")


class PetitionSignature(db.Model):
    __tablename__ = "petition_signatures"

    id = db.Column(db.Integer, primary_key=True)
    petition_id = db.Column(db.Integer, db.ForeignKey("petitions.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # 👈 corretto
    signed_at = db.Column(db.DateTime, default=datetime.utcnow)

    petition = db.relationship("Petition", back_populates="signatures")
    user = db.relationship("User")


class PetitionSupport(db.Model):
    __tablename__ = "petition_supports"

    id = db.Column(db.Integer, primary_key=True)
    petition_id = db.Column(db.Integer, db.ForeignKey("petitions.id"), nullable=False)
    association_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # 👈 corretto
    supported_at = db.Column(db.DateTime, default=datetime.utcnow)

    petition = db.relationship("Petition", back_populates="supports")
    association = db.relationship("User")
