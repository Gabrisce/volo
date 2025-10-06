# app/blueprints/associations/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db

# Modelli (rispettano i tuoi path)
from app.database.models.user import User
from app.database.models.post import Post
from app.database.models.event import Event
from app.database.models.campaign import Campaign

associations_bp = Blueprint("associations", __name__, url_prefix="/associations")


# 🔍 Elenco di tutte le associazioni
@associations_bp.route("/associazioni")
@login_required
def list_associations():
    associations = (
        User.query.filter_by(user_type="association")
        .order_by(User.name.asc())
        .all()
    )
    return render_template("pages/associations_list.html", associations=associations)


# ➕ Segui un'associazione (solo volontari)
@associations_bp.route("/associazioni/<int:association_id>/follow", methods=["POST"])
@login_required
def follow_association(association_id: int):
    association = User.query.get_or_404(association_id)

    if current_user.user_type != "volunteer":
        flash("Solo i volontari possono seguire le associazioni.", "warning")
        return redirect(url_for("associations.public_profile", association_id=association_id))

    if association.user_type != "association":
        flash("Puoi seguire solo le associazioni.", "danger")
        return redirect(url_for("associations.list_associations"))

    if association not in current_user.followed_associations:
        current_user.followed_associations.append(association)
        db.session.commit()
        flash(f"Hai iniziato a seguire {association.name}.", "success")

    return redirect(url_for("associations.public_profile", association_id=association_id))


# ➖ Smetti di seguire
@associations_bp.route("/associazioni/<int:association_id>/unfollow", methods=["POST"])
@login_required
def unfollow_association(association_id: int):
    association = User.query.get_or_404(association_id)

    if current_user.user_type != "volunteer":
        flash("Solo i volontari possono smettere di seguire le associazioni.", "warning")
        return redirect(url_for("associations.public_profile", association_id=association_id))

    if association.user_type != "association":
        flash("Puoi smettere di seguire solo le associazioni.", "danger")
        return redirect(url_for("associations.list_associations"))

    if association in current_user.followed_associations:
        current_user.followed_associations.remove(association)
        db.session.commit()
        flash(f"Hai smesso di seguire {association.name}.", "info")

    return redirect(url_for("associations.public_profile", association_id=association_id))


# 👤 Profilo pubblico di una singola associazione
@associations_bp.route("/associazioni/<int:association_id>")
def public_profile(association_id: int):
    association = User.query.get_or_404(association_id)
    if association.user_type != "association":
        abort(404)

    events = (
        Event.query.filter_by(association_id=association.id)
        .order_by(Event.date.desc())
        .all()
    )
    posts = (
        Post.query.filter_by(association_id=association.id)
        .order_by(Post.created_at.desc())
        .all()
    )
    campaigns = (
        Campaign.query.filter_by(association_id=association.id)
        .order_by(Campaign.created_at.desc())
        .all()
    )

    return render_template(
        "pages/association_profile.html",
        association=association,
        events=events,
        posts=posts,
        campaigns=campaigns,
    )


# 📄 Pagina di dettaglio dinamica (evento, campagna o post)
@associations_bp.route("/detail/<string:content_type>/<int:item_id>")
def detail(content_type: str, item_id: int):
    """
    Mostra la pagina di dettaglio per:
    - Evento   → /associations/detail/event/<id>
    - Campagna → /associations/detail/campaign/<id>
    - Post     → /associations/detail/post/<id>
    """
    model_map = {"event": Event, "campaign": Campaign, "post": Post}
    model = model_map.get(content_type)
    if not model:
        abort(404)

    item = model.query.get_or_404(item_id)

    # (Facoltativo) calcolo capienza per EVENTI e la passo al template
    capacity = None
    if content_type == "event":
        total_seats = item.capacity_max  # None -> illimitati
        try:
            accepted_count = len([p for p in item.participants if getattr(p, "status", "accepted") == "accepted"])
        except Exception:
            accepted_count = len(getattr(item, "participants", []) or [])
        seats_left = (total_seats - accepted_count) if total_seats is not None else None
        is_full = (total_seats is not None and seats_left is not None and seats_left <= 0)
        capacity = {
            "total": total_seats,
            "accepted": accepted_count,
            "left": seats_left,
            "is_full": is_full,
        }

    return render_template(
        "pages/detail.html",
        type=content_type,
        item=item,
        capacity=capacity,
    )
