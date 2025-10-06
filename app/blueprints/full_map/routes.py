# app/blueprints/full_map/routes.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Blueprint, render_template, url_for
from flask_login import login_required

from app.database.models.event import Event
from app.database.models.campaign import Campaign
from app.database.models.report import Report
from app.database.models.petition import Petition
from sqlalchemy import and_

# ---- Blueprint ----
STATIC_ROOT = Path(__file__).resolve().parent.parent / "blueprints" / "static"
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

full_map_bp = Blueprint(
    "full_map",
    __name__,
    url_prefix="/map",
    static_folder=str(STATIC_ROOT),
    static_url_path="/map/static",
)

# ---- Helpers ----
def _get_lat(obj) -> Optional[float]:
    val = getattr(obj, "latitude", None)
    if val is None:
        val = getattr(obj, "lat", None)
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None

def _get_lng(obj) -> Optional[float]:
    val = getattr(obj, "longitude", None)
    if val is None:
        val = getattr(obj, "lng", None)
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None

def _has_latlng_model_fields(model) -> str:
    """
    Ritorna "latlng" se il modello ha campi lat/lng,
            "latitude_longitude" se ha latitude/longitude,
            "" se nessuno dei due.
    """
    if hasattr(model, "lat") and hasattr(model, "lng"):
        return "latlng"
    if hasattr(model, "latitude") and hasattr(model, "longitude"):
        return "latitude_longitude"
    return ""

# ---- Serializers ----
def _serialize_event_for_map(e: Event) -> Dict[str, Any]:
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "date": e.date.isoformat() if getattr(e, "date", None) else None,
        "latitude": _get_lat(e),
        "longitude": _get_lng(e),
        "type": "event",
        "location": getattr(e, "location", None),
        "image_filename": getattr(e, "image_filename", None),
        "url": url_for("events.event_detail", event_id=e.id),
    }

def _serialize_campaign_for_map(c: Campaign) -> Dict[str, Any]:
    return {
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "date": c.created_at.isoformat() if getattr(c, "created_at", None) else None,
        "latitude": _get_lat(c),
        "longitude": _get_lng(c),
        "type": "campaign",
        "location": getattr(c, "location", None),
        "image_filename": getattr(c, "image_filename", None),
        "url": url_for("campaigns.campaign_detail", campaign_id=c.id),
    }

def _serialize_report_for_map(r: Report) -> Dict[str, Any]:
    return {
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "date": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
        "latitude": _get_lat(r),
        "longitude": _get_lng(r),
        "type": "report",
        "location": getattr(r, "location", None),
        "image_filename": getattr(r, "image_filename", None),
        "url": url_for("public.detail", content_type="report", item_id=r.id),
    }

def _serialize_petition_for_map(p: Petition) -> Dict[str, Any]:
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "date": p.created_at.isoformat() if getattr(p, "created_at", None) else None,
        "latitude": _get_lat(p),       # normalizzato a float
        "longitude": _get_lng(p),      # normalizzato a float
        "type": "petition",
        "location": getattr(p, "location", None),
        "image_filename": getattr(p, "image_filename", None),
        "url": url_for("petitions.petition_detail", petition_id=p.id),
    }

# ---- Routes ----
@full_map_bp.route("/", methods=["GET"])
@login_required
def full_map():
    # Eventi e campagne: tieni il filtro con coordinate (sono sempre geolocalizzati)
    events = Event.query.filter(
        Event.latitude.isnot(None), Event.longitude.isnot(None)
    ).all()
    campaigns = Campaign.query.filter(
        Campaign.latitude.isnot(None), Campaign.longitude.isnot(None)
    ).all()

    # Report: considerali geolocalizzati (come da UI) – se i campi si chiamano diversamente, usa l'altro filtro
    reports_fieldset = _has_latlng_model_fields(Report)
    if reports_fieldset == "latitude_longitude":
        reports = Report.query.filter(
            Report.latitude.isnot(None), Report.longitude.isnot(None)
        ).all()
    elif reports_fieldset == "latlng":
        reports = Report.query.filter(
            Report.lat.isnot(None), Report.lng.isnot(None)
        ).all()
    else:
        reports = []  # nessun campo coord nel modello

    # Petizioni: DEVONO essere sempre localizzate → filtra per i campi che hai realmente
    petitions_fieldset = _has_latlng_model_fields(Petition)
    if petitions_fieldset == "latitude_longitude":
        petitions = Petition.query.filter(
            Petition.latitude.isnot(None), Petition.longitude.isnot(None)
        ).all()
    elif petitions_fieldset == "latlng":
        petitions = Petition.query.filter(
            Petition.lat.isnot(None), Petition.lng.isnot(None)
        ).all()
    else:
        petitions = []  # modello senza coord: così non ne passiamo nessuna (coerente col requisito)

    return render_template(
        "pages/full_map.html",
        events=[_serialize_event_for_map(e) for e in events],
        campaigns=[_serialize_campaign_for_map(c) for c in campaigns],
        reports=[_serialize_report_for_map(r) for r in reports],
        petitions=[_serialize_petition_for_map(p) for p in petitions],
    )
