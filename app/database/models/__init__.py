# app/database/models/__init__.py
"""Aggregate all database models for easy import."""

from .user import User
from .event import Event
from .campaign import Campaign
from .post import Post
from .report import Report
from .donation import Donation
from .participation import Participation
from .notification import Notification
from .chat import Chat
from .applause import Applause
from .petition import Petition, PetitionSignature, PetitionSupport


__all__ = [
    "User",
    "Event",
    "Campaign",
    "Post",
    "Report",
    "Donation",
    "Participation",
    "Notification",
    "Chat",
]
