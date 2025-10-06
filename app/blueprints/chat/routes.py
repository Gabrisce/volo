from flask import Blueprint, jsonify, render_template, abort
from flask_login import login_required, current_user
from app import db
from app.database.models.user import User
from app.database.models.chat import Chat

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

# Avvia conversazione (o recupera quella già esistente)
@chat_bp.route("/start/<int:user_id>")
@login_required
def start_chat(user_id):
    other = User.query.get_or_404(user_id)

    # Impediamo di avviare chat con se stessi
    if other.id == current_user.id:
        abort(400, description="Non puoi avviare una chat con te stesso.")

    # Ordiniamo sempre la coppia (per rispettare UniqueConstraint)
    u1, u2 = sorted([current_user.id, other.id])

    chat = Chat.query.filter_by(user1_id=u1, user2_id=u2).first()
    if not chat:
        chat = Chat(user1_id=u1, user2_id=u2)
        db.session.add(chat)
        db.session.commit()

    # Ritorna un template che include il partial della chat
    return render_template("pages/chat.html", other=other, chat=chat)


# API → lista conversazioni dell’utente loggato (usata da chat.html via JS)
@chat_bp.route("/api/conversations")
@login_required
def list_conversations():
    chats = Chat.query.filter(
        (Chat.user1_id == current_user.id) | (Chat.user2_id == current_user.id)
    ).all()

    results = []
    for c in chats:
        other_id = c.user2_id if c.user1_id == current_user.id else c.user1_id
        other = User.query.get(other_id)
        if not other:
            continue
        results.append({
            "id": other.id,
            "name": other.name,
            "photo": (
                f"/static/uploads/profile-photo/{other.photo_filename}"
                if other.photo_filename else "/static/img/avatar-placeholder.png"
            ),
        })

    return jsonify(results)
