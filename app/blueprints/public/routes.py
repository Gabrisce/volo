# app/blueprints/public/routes.py

from flask import Blueprint, render_template, abort, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.database.models.user import User
from app.database.models.post import Post
from app.database.models.event import Event
from app.database.models.donation import Donation
from app.database.models.campaign import Campaign
from app.database.models.report import Report   # 👈 aggiunto import
from app.database.models.chat import Chat
from datetime import datetime
from sqlalchemy.orm import joinedload


public_bp = Blueprint("public", __name__)


# 🔍 Elenco di tutte le associazioni
@public_bp.route("/associazioni")
def list_associations():
    associations = (
        User.query.filter_by(user_type="association")
        .order_by(User.name.asc())
        .all()
    )
    return render_template(
        "pages/associations_list.html", associations=associations
    )


@public_bp.route("/associazioni/<int:association_id>/follow", methods=["POST"])
@login_required
def follow_association(association_id):
    association = User.query.get_or_404(association_id)

    # ✅ Solo volontari possono seguire
    if current_user.user_type != "volunteer":
        flash("Solo i volontari possono seguire le associazioni.", "warning")
        return redirect(
            url_for("public.public_profile", association_id=association_id)
        )

    # ✅ Puoi seguire solo associazioni
    if association.user_type != "association":
        flash("Puoi seguire solo le associazioni.", "danger")
        return redirect(url_for("public.list_associations"))

    if association not in current_user.followed_associations:
        current_user.followed_associations.append(association)
        db.session.commit()
        flash(f"Hai iniziato a seguire {association.name}", "success")

    return redirect(
        url_for("public.public_profile", association_id=association_id)
    )


@public_bp.route("/associazioni/<int:association_id>/unfollow", methods=["POST"])
@login_required
def unfollow_association(association_id):
    association = User.query.get_or_404(association_id)

    if current_user.user_type != "volunteer":
        flash(
            "Solo i volontari possono smettere di seguire le associazioni.",
            "warning",
        )
        return redirect(
            url_for("public.public_profile", association_id=association_id)
        )

    if association.user_type != "association":
        flash("Puoi smettere di seguire solo le associazioni.", "danger")
        return redirect(url_for("public.list_associations"))

    if association in current_user.followed_associations:
        current_user.followed_associations.remove(association)
        db.session.commit()
        flash(f"Hai smesso di seguire {association.name}", "info")

    return redirect(
        url_for("public.public_profile", association_id=association_id)
    )
# 👤 Profilo pubblico di una singola associazione
@public_bp.route("/associazioni/<int:association_id>")
def public_profile(association_id):
    from datetime import datetime
    from sqlalchemy.orm import joinedload

    association = User.query.get_or_404(association_id)
    if association.user_type != "association":
        abort(404)

    now = datetime.utcnow()

    # subito dopo aver ottenuto 'association' e 'now'
    is_following = False
    if current_user.is_authenticated and current_user.id != association.id:
        fa = getattr(current_user, "followed_associations", None)
    try:
        if fa is not None:
            # se è una relazione dynamic (Query)
            if hasattr(fa, "filter_by"):
                is_following = fa.filter_by(id=association.id).count() > 0
            else:
                # se è una lista già caricata
                is_following = any(getattr(a, "id", None) == association.id for a in fa)
    except Exception:
        is_following = False

    # helper: primo campo data non nullo tra una lista
    def first_dt(obj, *names):
        for n in names:
            val = getattr(obj, n, None)
            if val:
                return val
        return None

    # --- Post ---
    posts = (
        Post.query.filter_by(association_id=association.id)
        .order_by(Post.created_at.desc())
        .all()
    )

    # --- Eventi (compatibili con modelli senza end_date) ---
    events = (
        Event.query.filter_by(association_id=association.id)
        .order_by(Event.date.desc())   # se 'date' non esistesse, puoi togliere l'order_by
        .all()
    )
    active_events, ended_events = [], []
    for e in events:
        start = first_dt(e, "date", "start_date", "starts_at", "start_at")
        end   = first_dt(e, "end_date", "end_at", "ends_at", "until", "deadline")
        if end:
            (active_events if end >= now else ended_events).append(e)
        else:
            # se non c'è end: consideralo attivo se deve ancora iniziare, altrimenti terminato
            if start and start >= now:
                active_events.append(e)
            else:
                ended_events.append(e)

    # --- Campagne (supporta anche modelli senza end_date) ---
    campaigns = (
        Campaign.query.filter_by(association_id=association.id)
        .order_by(Campaign.created_at.desc())
        .all()
    )
    active_campaigns, ended_campaigns = [], []
    for c in campaigns:
        c_end = first_dt(c, "end_date", "deadline", "end_at", "ends_at", "close_date")
        if c_end and c_end < now:
            ended_campaigns.append(c)
        else:
            active_campaigns.append(c)

    # --- Storico: SOLO terminati (eventi + campagne) ---
    history_items = []
    # Eventi terminati, ordinati per fine o in alternativa per inizio
    history_items.extend(
        {
            "type": "event",
            "event_id": e.id,
            "title": e.title,
            "date": first_dt(e, "end_date", "end_at", "ends_at", "date", "start_date", "starts_at", "start_at"),
            "location": getattr(e, "location", None),
        }
        for e in sorted(
            ended_events,
            key=lambda x: first_dt(x, "end_date", "end_at", "ends_at", "date", "start_date", "starts_at", "start_at") or now,
            reverse=True,
        )
    )
    # Campagne terminate, ordinate per fine
    history_items.extend(
        {
            "type": "campaign",
            "campaign_id": c.id,
            "title": c.title,
            "date": first_dt(c, "end_date", "deadline", "end_at", "ends_at", "close_date"),
            "goal": getattr(c, "goal", None) or getattr(c, "goal_amount", None),
        }
        for c in sorted(
            ended_campaigns,
            key=lambda x: first_dt(x, "end_date", "deadline", "end_at", "ends_at", "close_date") or now,
            reverse=True,
        )
    )

    # --- Donazioni ricevute (Campaign -> Donation) ---
    donations = (
        Donation.query
        .options(joinedload(Donation.campaign), joinedload(Donation.user))
        .join(Campaign, Campaign.id == Donation.campaign_id)
        .filter(Campaign.association_id == association.id)
        .order_by(Donation.created_at.desc())
        .all()
    )

    return render_template(
        "pages/association_profile.html",
        association=association,
        posts=posts,
        donations=donations,
        history_items=history_items,
        active_events=active_events,
        active_campaigns=active_campaigns,
        # opzionali, se ti servono altrove
        events=events,
        campaigns=campaigns,
        is_following=is_following, 
        now=now,
    )





@public_bp.route("/associazioni/seguiti")
@login_required
def followed_associations():
    # Prende sempre le associazioni seguite dall'utente corrente
    associations = current_user.followed_associations.all()

    return render_template(
        "pages/followed_associations.html",
        associations=associations,
    )

@public_bp.route("/volontari/<int:volunteer_id>/associazioni-seguite")
@login_required
def volunteer_followed_associations(volunteer_id):
    volunteer = User.query.get_or_404(volunteer_id)

    if volunteer.user_type != "volunteer":
        flash("Questo utente non è un volontario.", "warning")
        return redirect(url_for("home.home"))

    associations = volunteer.followed_associations.all()

    return render_template(
        "pages/followed_associations.html",
        associations=associations,
        volunteer=volunteer
    )

# 📄 Pagina di dettaglio dinamica (evento, campagna, post, segnalazione)
@public_bp.route("/detail/<string:content_type>/<int:item_id>")
def detail(content_type, item_id):
    """
    Mostra la pagina di dettaglio per:
    - Evento       → /public/detail/event/1
    - Campagna     → /public/detail/campaign/2
    - Segnalazione → /public/detail/report/4
    """
    model_map = {
        "event": Event,
        "campaign": Campaign,
        "report": Report,
    }

    model = model_map.get(content_type)
    if not model:
        abort(404)

    item = model.query.get_or_404(item_id)

    # 🔗 Campagne correlate solo se è un evento
    related_campaigns = []
    if content_type == "event":
        related_campaigns = (
            Campaign.query
            .filter(
                Campaign.association_id == item.association_id,
                (Campaign.end_date.is_(None)) | (Campaign.end_date >= datetime.utcnow())
            )
            .order_by(Campaign.created_at.desc())
            .limit(3)
            .all()
        )

    return render_template(
        "pages/detail.html",
        item=item,
        type=content_type,
        related_campaigns=related_campaigns
    )



# 💬 API: elenco conversazioni dell'utente corrente
@public_bp.route("/api/conversations")
@login_required
def api_conversations():
    chats = Chat.query.filter(
        (Chat.user1_id == current_user.id)
        | (Chat.user2_id == current_user.id)
    ).all()

    users = []
    for chat in chats:
        other_id = (
            chat.user1_id
            if chat.user2_id == current_user.id
            else chat.user2_id
        )
        user = User.query.get(other_id)
        if user:
            users.append(user)

    return jsonify(
        [
            {
                "id": u.id,
                "name": u.name,
                "photo": url_for(
                    "dashboard.static",
                    filename="uploads/profile-photo/" + u.photo_filename,
                )
                if u.photo_filename
                else url_for(
                    "static", filename="img/avatar-placeholder.png"
                ),
            }
            for u in users
        ]
    )


# 💬 API: crea una nuova chat (se non esiste già)
@public_bp.route("/api/start_chat/<int:other_id>", methods=["POST"])
@login_required
def start_chat(other_id):
    # Evita chat con se stesso
    if other_id == current_user.id:
        return jsonify({"success": False, "error": "Non puoi chattare con te stesso."}), 400

    # Verifica se esiste già
    existing = Chat.query.filter(
        ((Chat.user1_id == current_user.id) & (Chat.user2_id == other_id))
        | ((Chat.user1_id == other_id) & (Chat.user2_id == current_user.id))
    ).first()

    if not existing:
        chat = Chat(user1_id=current_user.id, user2_id=other_id)
        db.session.add(chat)
        db.session.commit()

    return jsonify({"success": True})


# Pagine statiche utility
@public_bp.route('/chisiamo')
def chisiamo():
    return render_template('utilities/chisiamo.html')

@public_bp.route('/contatti')
def contatti():
    return render_template('utilities/contatti.html')

@public_bp.route('/terms')
def terms():
    return render_template('utilities/terms.html')

@public_bp.route('/privacy')
def privacy():
    return render_template('utilities/privacy.html')

@public_bp.route("/faq")
def faq():
    return render_template("utilities/faq.html")

