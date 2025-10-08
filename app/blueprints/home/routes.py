# app/blueprints/home/routes.py
from flask import Blueprint, render_template, request
from flask_login import login_required
from app.database.models.user import User
from app.utils.feed import get_feed_items, collect_search_text, matches_query
from app.database.models.petition import Petition



home_bp = Blueprint("home", __name__, url_prefix="/")

@home_bp.route("", methods=["GET"])
@login_required
def home():
    q = (request.args.get('q') or '').strip()
    types = request.args.getlist('type')
    assoc_ids = request.args.getlist('association_id')
    petitions = Petition.query.order_by(Petition.created_at.desc()).all()


    associations_options = [
        {"id": u.id, "name": u.name}
        for u in User.query.filter(User.user_type == "association").order_by(User.name.asc()).all()
    ]

    feed_items = get_feed_items()

    # Filtri
    if types:
        feed_items = [it for it in feed_items if it.get("type") in types]

    if assoc_ids:
        def _belongs(it):
            obj = it.get("item")
            if not obj:
                return False
            assoc = getattr(obj, "association", None)
            if assoc and getattr(assoc, "id", None):
                return str(assoc.id) in assoc_ids
            assoc_fk = getattr(obj, "association_id", None)
            return str(assoc_fk) in assoc_ids if assoc_fk else False
        feed_items = [it for it in feed_items if _belongs(it)]

    if q:
        def _matches(it):
            obj = it.get('item')
            return obj and matches_query(collect_search_text(obj), q)
        feed_items = [it for it in feed_items if _matches(it)]
        found_associations = User.query.filter(
            User.user_type == 'association',
            User.name.ilike(f"%{q}%"),
        ).all()
    else:
        found_associations = []

    associations = (
        User.query
        .filter(User.user_type == 'association')
        # facoltativo: tieni solo chi ha coordinate (per il sort per distanza lato client)
        # .filter(User.latitude.isnot(None), User.longitude.isnot(None))
        .order_by(User.name.asc())   # o .order_by(User.created_at.desc())
        .limit(50)                   # evita carichi inutili
        .all()
    )

    return render_template(
        "pages/home.html",
        feed_items=feed_items,
        found_associations=found_associations,
        associations=associations,
        associations_options=associations_options,
        petitions=petitions,  # 👈 passa la lista al template
    )
