# app/blueprints/events/routes.py
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import unicodedata

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    jsonify,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.blueprints.events.forms import EventForm
from app.database.models.event import Event
from app.database.models.user import User
from app.database.models.report import Report
from app.database.models.campaign import Campaign
from app.utils.feed import get_feed_items
from app.database.models.participation import Participation
from app.database.models.notification import Notification

import sqlalchemy as sa

# -----------------------------------------------------------------------------
# Blueprint (URL prefix + static dei blueprint)
# -----------------------------------------------------------------------------
# Tutti i file statici devono vivere in app/blueprints/static/...
STATIC_ROOT = Path(__file__).resolve().parent.parent / "blueprints" / "static"
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

events_bp = Blueprint(
    "events",
    __name__,
    url_prefix="/events",
    static_folder=str(STATIC_ROOT),   # serve app/blueprints/static
    static_url_path="/events/static"  # endpoint: events.static
)

# -----------------------------------------------------------------------------
# Upload paths
# -----------------------------------------------------------------------------
EVENTS_UPLOAD_FOLDER = STATIC_ROOT / "uploads" / "events"
EVENTS_UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
EVENTS_URL_PATH = "uploads/events"  # per eventuali riferimenti nei template

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _safe_str(v: Optional[str]) -> str:
    return (v or "").strip().lower()

def _normalize(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


# ---- colonne dinamiche sull'Event -------------------------------------------
def _event_has_col(name: str) -> bool:
    try:
        return name in Event.__table__.c  # type: ignore[attr-defined]
    except Exception:
        return False

def _is_skills_json_column() -> bool:
    if not _event_has_col("skills"):
        return False
    try:
        return isinstance(Event.__table__.c.skills.type, sa.JSON)  # type: ignore[attr-defined]
    except Exception:
        return False

def _parse_skills_from_request() -> List[str]:
    items = request.form.getlist("skills")
    if not items:
        raw = request.form.get("skills", "")
        if raw:
            items = [p.strip() for p in raw.split(",")]
    clean: List[str] = []
    for s in items:
        s = s.strip()
        if s and s not in clean:
            clean.append(s)
    return clean

def _coerce_skills_for_db(skills_list: List[str]):
    if not _event_has_col("skills"):
        return None
    if _is_skills_json_column():
        return skills_list or []
    return ",".join(skills_list) if skills_list else ""

def _get_duration_from_request(default: str = "temporary") -> Optional[str]:
    if not _event_has_col("duration"):
        return None
    val = (request.form.get("duration") or "").strip().lower()
    return val if val in {"temporary", "perennial"} else default

def _get_type_from_request(default: str = "general") -> Optional[str]:
    if not _event_has_col("type"):
        return None
    val = (request.form.get("type") or "").strip().lower()
    return val or default

def _get_activity_from_request() -> Optional[str]:
    if not _event_has_col("activity"):
        return None
    val = (request.form.get("activity") or "").strip()
    return val or None


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@events_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_event():
    if current_user.user_type != "association":
        abort(403)

    form = EventForm()
    if form.validate_on_submit():
        lat = request.form.get("latitude")
        lng = request.form.get("longitude")

        # immagine (opzionale)
        filename: Optional[str] = None
        image_file = form.image.data
        if image_file:
            raw_filename = secure_filename(image_file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{raw_filename}"
            image_path = EVENTS_UPLOAD_FOLDER / filename
            image_file.save(str(image_path))

        # nuovi campi (solo se esistono a DB)
        duration = _get_duration_from_request()
        ev_type = _get_type_from_request()
        activity = _get_activity_from_request()
        skills_list = _parse_skills_from_request()
        skills_value = _coerce_skills_for_db(skills_list)

        event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            location=form.location.data,
            latitude=float(lat) if lat else None,
            longitude=float(lng) if lng else None,
            image_filename=filename,
            association_id=current_user.id,
        )

        # setta dinamicamente i campi opzionali
        if duration is not None:
            event.duration = duration  # type: ignore[attr-defined]
        if ev_type is not None:
            event.type = ev_type  # type: ignore[attr-defined]
        if activity is not None:
            event.activity = activity  # type: ignore[attr-defined]
        if skills_value is not None:
            event.skills = skills_value  # type: ignore[attr-defined]
        if _event_has_col("updated_at"):
            event.updated_at = datetime.utcnow()  # type: ignore[attr-defined]

        db.session.add(event)
        db.session.commit()
        flash("Evento creato con successo!", "success")
        return redirect(url_for("events.my_events"))

    return render_template("pages/event_form.html", form=form, edit=False)


@events_bp.route("/edit/<int:event_id>", methods=["GET", "POST"])
@login_required
def edit_event(event_id: int):
    event: Event = Event.query.get_or_404(event_id)

    if current_user.user_type != "association" or event.association_id != current_user.id:
        abort(403)

    form = EventForm(obj=event)
    if form.validate_on_submit():
        lat = request.form.get("latitude")
        lng = request.form.get("longitude")

        image_file = form.image.data
        if image_file:
            raw_filename = secure_filename(image_file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{raw_filename}"
            image_path = EVENTS_UPLOAD_FOLDER / filename
            image_file.save(str(image_path))
            event.image_filename = filename

        # aggiorna i campi manualmente (escludendo latitude/longitude dal populate_obj)
        event.title = form.title.data
        event.description = form.description.data
        event.date = form.date.data
        event.location = form.location.data

        # aggiorna coordinate solo se valorizzate
        event.latitude = float(lat) if lat and lat.strip() != "" else event.latitude
        event.longitude = float(lng) if lng and lng.strip() != "" else event.longitude

        # campi opzionali
        duration = _get_duration_from_request(event.duration if _event_has_col("duration") else "temporary")  # type: ignore[attr-defined]
        if duration is not None:
            event.duration = duration  # type: ignore[attr-defined]

        ev_type = _get_type_from_request(event.type if _event_has_col("type") else "general")  # type: ignore[attr-defined]
        if ev_type is not None:
            event.type = ev_type  # type: ignore[attr-defined]

        activity = _get_activity_from_request()
        if activity is not None:
            event.activity = activity  # type: ignore[attr-defined]

        skills_list = _parse_skills_from_request()
        if skills_list:
            coerced = _coerce_skills_for_db(skills_list)
            if coerced is not None:
                event.skills = coerced  # type: ignore[attr-defined]

        if _event_has_col("updated_at"):
            event.updated_at = datetime.utcnow()  # type: ignore[attr-defined]

        # aggiorna capacity_max manualmente
        if hasattr(form, "capacity_mode") and hasattr(form, "capacity_max"):
            if form.capacity_mode.data == "limited":
                event.capacity_max = form.capacity_max.data
            else:
                event.capacity_max = None

        db.session.commit()
        flash("Evento aggiornato con successo!", "success")
        return redirect(url_for("events.my_events"))

    return render_template("pages/event_form.html", form=form, edit=True, event=event)



@events_bp.route("/<int:event_id>/apply", methods=["GET"])
@login_required
def apply(event_id: int):
    if current_user.user_type != "volunteer":
        abort(403)

    event = Event.query.get_or_404(event_id)
    return render_template("pages/confirm_participation.html", event=event)


@events_bp.route("/my", methods=["GET"])
@login_required
def my_events():
    if current_user.user_type != "association":
        abort(403)

    my_events = (
        Event.query.filter_by(association_id=current_user.id)
        .order_by(Event.date.asc())
        .all()
    )
    return render_template("pages/my_events.html", events=my_events)


@events_bp.route("/api", methods=["GET"])
def api_events():
    events = Event.query.filter(
        Event.latitude.isnot(None), Event.longitude.isnot(None)
    ).all()
    campaigns = Campaign.query.filter(
        Campaign.latitude.isnot(None), Campaign.longitude.isnot(None)
    ).all()

    payload: List[Dict[str, Any]] = []
    for e in events:
        payload.append(
            {
                "id": e.id,
                "type": "event",
                "name": e.title,
                "title": e.title,
                "latitude": e.latitude,
                "longitude": e.longitude,
                "description": e.description,
                "location": e.location,
                "image_filename": e.image_filename,
                "url": url_for("events.event_detail", event_id=e.id),
            }
        )
    for c in campaigns:
        payload.append(
            {
                "id": c.id,
                "type": "campaign",
                "name": c.title,
                "title": c.title,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "description": c.description,
                "location": c.location,
                "image_filename": c.image_filename,
                "url": url_for("campaigns.campaign_detail", campaign_id=c.id),
            }
        )

    return jsonify(payload)


@events_bp.route("/<int:event_id>", methods=["GET"])
@login_required
def event_detail(event_id: int):
    event = Event.query.get_or_404(event_id)
    return render_template("pages/detail.html", item=event, type="event")


@events_bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id: int):
    event = Event.query.get_or_404(event_id)

    if current_user.user_type != "association" or event.association_id != current_user.id:
        abort(403)

    db.session.delete(event)
    db.session.commit()
    flash("Evento eliminato con successo", "success")
    return redirect(url_for("dashboard.dashboard_association"))


@events_bp.route("/<int:event_id>/confirm", methods=["POST"])
@login_required
def confirm_participation(event_id: int):
    if current_user.user_type != "volunteer":
        abort(403)

    event = Event.query.get_or_404(event_id)

    # Controllo capienza massima
    if event.is_full():
        flash("⚠️ Questo evento ha già raggiunto il numero massimo di partecipanti.", "warning")
        return redirect(url_for("events.event_detail", event_id=event_id))

    existing = Participation.query.filter_by(
        volunteer_id=current_user.id,
        event_id=event.id
    ).first()

    if existing:
        flash("Hai già inviato una candidatura per questo evento.", "info")
    else:
        participation = Participation(volunteer_id=current_user.id, event_id=event.id)
        db.session.add(participation)

        # 🔔 Notifica per l’associazione organizzatrice
        notif = Notification(
            user_id=event.association_id,
            type="participation_request",
            message=f"{current_user.name} si è candidato all’evento '{event.title}'",
            url=url_for("events.participants", event_id=event.id)
        )
        db.session.add(notif)

        db.session.commit()
        flash("Candidatura inviata con successo!", "success")

    return redirect(url_for("events.event_detail", event_id=event_id))


@events_bp.route("/<int:event_id>/cancel", methods=["POST"])
@login_required
def cancel(event_id: int):
    if current_user.user_type != "volunteer":
        abort(403)

    part = Participation.query.filter_by(
        volunteer_id=current_user.id,
        event_id=event_id
    ).first_or_404()

    db.session.delete(part)
    db.session.commit()
    flash("Hai annullato la tua partecipazione.", "info")
    return redirect(url_for("events.event_detail", event_id=event_id))


@events_bp.route("/<int:event_id>/participants", methods=["GET"])
@login_required
def participants(event_id: int):
    event = Event.query.get_or_404(event_id)

    if current_user.user_type != "association" or event.association_id != current_user.id:
        abort(403)

    participations = Participation.query.filter_by(event_id=event.id).all()
    return render_template("pages/participants.html", event=event, participations=participations)


@events_bp.route("/<int:event_id>/participants/<int:part_id>/<string:action>", methods=["POST"])
@login_required
def update_participation(event_id: int, part_id: int, action: str):
    event = Event.query.get_or_404(event_id)
    part = Participation.query.get_or_404(part_id)

    if current_user.user_type != "association" or event.association_id != current_user.id:
        abort(403)

    old_status = part.status  # salviamo lo stato precedente

    if action == "accept":
        part.status = "accepted"
        flash("Volontario accettato!", "success")

        # notifica al volontario
        notif = Notification(
            user_id=part.volunteer_id,
            type="participation_update",
            message=f"Sei stato ACCETTATO all’evento '{event.title}'",
            url=url_for("events.event_detail", event_id=event.id)
        )
        db.session.add(notif)

    elif action == "reject":
        part.status = "rejected"
        flash("Volontario rifiutato.", "warning")

        # notifica al volontario
        notif = Notification(
            user_id=part.volunteer_id,
            type="participation_update",
            message=f"Sei stato RIFIUTATO all’evento '{event.title}'",
            url=url_for("events.event_detail", event_id=event.id)
        )
        db.session.add(notif)

    # Se cambia da accettato a rifiutato o viceversa, viene comunque intercettato qui,
    # perché aggiorniamo sempre lo stato e generiamo la notifica.

    db.session.commit()
    return redirect(url_for("events.participants", event_id=event_id))
