# app/database/models/user.py
from app import db
from flask_login import UserMixin

# Association table for many-to-many relation: volunteers-associations
follows = db.Table(
    "follows",
    db.Column("volunteer_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("association_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
)


class User(db.Model, UserMixin):
    """User model for volunteers and associations."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    # Authentication
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(256), nullable=False)

    # Identity
    name = db.Column(db.String(150), nullable=False)   # Full name or organization name
    user_type = db.Column(db.String(20), nullable=False, index=True)  # "volunteer" | "association"

    # Volunteer profile fields
    date_of_birth = db.Column(db.Date, nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    photo_filename = db.Column(db.String(255), nullable=True)
    disponibilita = db.Column(db.Text, nullable=True)  # Availability (days/times)

    # Association profile fields
    address = db.Column(db.String(255), nullable=True)
    logo_filename = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    iban = db.Column(db.String(34), nullable=True)
    official_docs = db.Column(db.String(255), nullable=True)

    # Consents
    consenso_dati = db.Column(db.Boolean, default=False, nullable=False)
    accetta_termini = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    posts = db.relationship("Post", backref="association", lazy=True)
    events = db.relationship("Event", back_populates="association", lazy=True)
    campaigns = db.relationship("Campaign", back_populates="association", lazy=True, cascade="all, delete-orphan")

    followed_associations = db.relationship(
        "User",
        secondary=follows,
        primaryjoin=(follows.c.volunteer_id == id),
        secondaryjoin=(follows.c.association_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )
    
    applause = db.relationship(
    "Applause",
    back_populates="user",
    cascade="all, delete-orphan",
    passive_deletes=True
    )


    def __repr__(self) -> str:
        return f"<User {self.name} ({self.user_type})>"
