# app/blueprints/notifications/routes.py
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app import db
from app.database.models.notification import Notification

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

# ✅ Segna tutte le notifiche come lette
@notifications_bp.route("/mark_all_read", methods=["POST"])
@login_required
def mark_all_read():
    unread = current_user.notifications.filter_by(is_read=False).all()
    for n in unread:
        n.is_read = True
    db.session.commit()
    return jsonify({"status": "ok", "cleared": len(unread)})
