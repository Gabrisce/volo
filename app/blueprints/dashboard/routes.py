import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.blueprints.dashboard.forms import ProfileForm
from app.blueprints.posts.forms import PostForm
from app.database.models.post import Post
from app.database.models.campaign import Campaign   # ✅ fix nome file/model
from app.database.models.event import Event        # ✅ fix nome file/model
from app.database.models.report import Report
from app.database.models.donation import Donation
from app.database.models.participation import Participation
from app.database.models.petition import Petition



dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard",
    template_folder="templates",
    static_folder="../static"
)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# 📁 Percorso assoluto per salvataggio foto profilo
UPLOAD_FOLDER_PROFILE_PHOTO = os.path.join(
    dashboard_bp.static_folder, "uploads", "profile-photo"
)
os.makedirs(UPLOAD_FOLDER_PROFILE_PHOTO, exist_ok=True)


# 🔎 --- Helper dedicato alle donazioni dell’utente ---------------------------
def _get_user_donations(user_id: int):
    return (
        Donation.query
        .filter(Donation.user_id == user_id)
        .order_by(Donation.created_at.desc())
        .all()
    )


# 🧭 Dashboard principale
@dashboard_bp.route("")
@login_required
def dashboard():
    if current_user.user_type == "association":
        return redirect(url_for("dashboard.dashboard_association"))
    return redirect(url_for("dashboard.dashboard_volunteer"))


@dashboard_bp.route("/volunteer")
@login_required
def dashboard_volunteer():
    if current_user.user_type != "volunteer":
        abort(403)

    # --- Attività create dal volontario (report e petizioni) ---
    activities = []

    reports = Report.query.filter_by(user_id=current_user.id).all()
    for r in reports:
        activities.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "created_at": r.created_at,
            "type": "report",
        })

    petitions = Petition.query.filter_by(user_id=current_user.id).all()
    for p in petitions:
        activities.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "created_at": p.created_at,
            "type": "petition",
        })

    activities = sorted(activities, key=lambda x: x["created_at"], reverse=True)

    # --- Donazioni ---
    donations = _get_user_donations(current_user.id)

   # --- Partecipazioni (tutte) ---
    participations = (
        Participation.query
        .join(Event)
        .filter(Participation.volunteer_id == current_user.id)
        .order_by(Event.date.desc())
        .all()
    )

    # 📅 Separa eventi in futuri e passati
    upcoming_participations = [p for p in participations if p.event.date > datetime.utcnow()]
    past_participations = [p for p in participations if p.event.date <= datetime.utcnow() and p.status == "accepted"]

    # --- Combina donazioni + eventi passati nello storico ---
    history_items = []

    # Aggiungi donazioni
    for d in donations:
        history_items.append({
            "type": "donation",
            "title": d.campaign.title if d.campaign else "Campagna",
            "date": d.created_at,
            "amount": d.amount,
            "pdf_filename": d.pdf_filename,
            "campaign_id": d.campaign.id if d.campaign else None,
        })

    # Aggiungi eventi passati
    for p in past_participations:
        history_items.append({
            "type": "event",
            "title": p.event.title,
            "date": p.event.date,
            "event_id": p.event.id,
            "location": p.event.location,
        })

    # Ordina per data decrescente
    history_items = sorted(history_items, key=lambda x: x["date"], reverse=True)

    return render_template(
        "pages/dashboard_volunteer.html",
        donations=donations,
        participations=upcoming_participations,
        activities=activities,
        history_items=history_items,
    )


# app/blueprints/dashboard/routes.py  (estratto)

@dashboard_bp.route("/association")
@login_required
def dashboard_association():
    if current_user.user_type != "association":
        abort(403)

    from datetime import datetime

    # 📌 Post dell’associazione
    posts = (
        Post.query.filter_by(association_id=current_user.id)
        .order_by(Post.created_at.desc())
        .all()
    )

    # 📅 Eventi dell’associazione
    my_events = (
        Event.query.filter_by(association_id=current_user.id)
        .order_by(Event.date.desc())
        .all()
    )

    # 🎯 Campagne dell’associazione
    my_campaigns = (
        Campaign.query.filter_by(association_id=current_user.id)
        .order_by(Campaign.created_at.desc())
        .all()
    )

    # 💰 Donazioni ricevute (restano nella tab Donazioni, non nello Storico)
    donations = (
        Donation.query.join(Campaign, Donation.campaign_id == Campaign.id)
        .filter(Campaign.association_id == current_user.id)
        .order_by(Donation.created_at.desc())
        .all()
    )

    # ===== Storico: Eventi già iniziati + Campagne terminate =====
    now = datetime.utcnow()

   # Evento TERMINATO:
    # - se c'è end_date  -> end_date < now
    # - se non c'è end_date -> considera terminato se la start date è passata di almeno 1 giorno
    #   (puoi cambiare la tolleranza a piacere, es. a poche ore)
    finished_events = [
        e for e in my_events
        if (
            getattr(e, "end_date", None) and e.end_date < now
        ) or (
            not getattr(e, "end_date", None)
            and getattr(e, "date", None)
            and e.date < (now - timedelta(days=1))
        )
    ]

    # Campagna TERMINATA: end_date esiste ed è < now
    ended_campaigns = [
        c for c in my_campaigns
        if getattr(c, "end_date", None) and c.end_date < now
    ]

    history_items = []

    for e in finished_events:
        # usa la data di fine se disponibile, altrimenti la start date per ordinare/mostrare
        display_date = getattr(e, "end_date", None) or getattr(e, "date", None) or now
        history_items.append({
            "type": "event",
            "title": e.title,
            "date": display_date,
            "event_id": e.id,
            "location": getattr(e, "location", None),
        })

    for c in ended_campaigns:
        history_items.append({
            "type": "campaign",
            "title": c.title,
            "date": c.end_date,     # data di fine campagna
            "campaign_id": c.id,
            "goal": getattr(c, "goal", None),
        })

    # ordina per data desc
    history_items.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        "pages/dashboard_association.html",
        posts=posts,
        my_events=my_events,
        my_campaigns=my_campaigns,
        donations=donations,
        history_items=history_items,
        now=now,
    )

# 🛠️ Modifica profilo
@dashboard_bp.route("/modify", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.age = form.age.data
        current_user.bio = form.bio.data

        # 📸 Gestione immagine profilo
        photo = form.photo.data
        if photo:
            filename = secure_filename(photo.filename)
            ext = filename.rsplit(".", 1)[-1].lower()

            if ext not in ALLOWED_EXTENSIONS:
                flash("Estensione non valida. Usa: jpg, jpeg, png.", "danger")
                return redirect(url_for("dashboard.edit_profile"))

            # 🔄 Elimina vecchia foto
            for old_ext in ALLOWED_EXTENSIONS:
                old_file = os.path.join(
                    UPLOAD_FOLDER_PROFILE_PHOTO, f"{current_user.id}.{old_ext}"
                )
                if os.path.exists(old_file):
                    os.remove(old_file)

            # 💾 Salva nuova foto
            new_filename = f"{current_user.id}.{ext}"
            save_path = os.path.join(UPLOAD_FOLDER_PROFILE_PHOTO, new_filename)
            photo.save(save_path)
            current_user.photo_filename = new_filename

        db.session.commit()
        flash("Profilo aggiornato con successo!", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("settings/edit_profile.html", form=form)


# 📝 Nuovo post
@dashboard_bp.route("/post/create", methods=["GET", "POST"])
@login_required
def create_post():
    if current_user.user_type != "association":
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(
            title=form.title.data,
            content=form.content.data,
            association_id=current_user.id,
        )
        db.session.add(new_post)
        db.session.commit()
        flash("Post pubblicato con successo!", "success")
        return redirect(url_for("dashboard.dashboard_association"))

    return render_template("pages/create_post.html", form=form)


# ✏️ Modifica post
@dashboard_bp.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    if current_user.user_type != "association":
        abort(403)

    post = Post.query.filter_by(
        id=post_id, association_id=current_user.id
    ).first_or_404()
    form = PostForm(obj=post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Post aggiornato con successo!", "success")
        return redirect(url_for("dashboard.dashboard_association"))

    return render_template("pages/post_form.html", form=form, post=post)


# 🗑️ Elimina post
@dashboard_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    if current_user.user_type != "association":
        abort(403)

    post = Post.query.filter_by(
        id=post_id, association_id=current_user.id
    ).first_or_404()
    db.session.delete(post)
    db.session.commit()
    flash("Post eliminato con successo!", "success")
    return redirect(url_for("dashboard.dashboard_association"))
