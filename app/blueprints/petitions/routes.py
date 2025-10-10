# app/blueprints/petitions/routes.py

import time
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.database.models.petition import Petition, PetitionSignature, PetitionSupport
from app.blueprints.petitions.forms import PetitionForm

# =============================================================================
# Config & paths
# =============================================================================
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

BASE_DIR = Path(__file__).resolve().parent           # .../app/blueprints/petitions
STATIC_FOLDER = BASE_DIR / "static"
PETITIONS_UPLOAD_FOLDER = STATIC_FOLDER / "uploads" / "petitions"
PETITIONS_UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

petitions_bp = Blueprint(
    "petitions",
    __name__,
    url_prefix="/petitions",
    static_folder=str(STATIC_FOLDER),
    static_url_path="/petitions/static",
    template_folder="templates",
)

# =============================================================================
# Helpers
# =============================================================================
def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS

def _unique_name(original: str) -> str:
    base = secure_filename(original)
    stem, dot, ext = base.partition(".")
    ts = int(time.time())
    return f"{current_user.id}_{ts}_{stem}.{ext}" if dot else f"{current_user.id}_{ts}_{base}"

def _save_image(file_storage, old_filename: str | None = None) -> str | None:
    """
    Salva una nuova immagine (se presente) e, se richiesto, elimina il vecchio file.
    Ritorna il nuovo filename (relativo alla cartella uploads/petitions) o quello vecchio
    se non viene caricata una nuova immagine.
    """
    if not file_storage or not getattr(file_storage, "filename", ""):
        return old_filename

    if not _allowed(file_storage.filename):
        flash("Formato immagine non valido. Usa jpg, jpeg, png o webp.", "danger")
        return old_filename

    # elimina il vecchio file se esiste
    if old_filename:
        try:
            (PETITIONS_UPLOAD_FOLDER / old_filename).unlink(missing_ok=True)
        except Exception:
            pass

    new_name = _unique_name(file_storage.filename)
    save_path = PETITIONS_UPLOAD_FOLDER / new_name
    file_storage.save(str(save_path))
    return new_name

def _parse_coord(value):
    """
    Converte '12,345' o '12.345' in float. Ritorna None se non valido.
    """
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None

# =============================================================================
# Create
# =============================================================================
@petitions_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_petition():
    form = PetitionForm()
    if form.validate_on_submit():
        lat = _parse_coord(form.latitude.data)
        lng = _parse_coord(form.longitude.data)
        if lat is None or lng is None:
            flash("Imposta correttamente la posizione sulla mappa.", "warning")
            return render_template("pages/petition_form.html", form=form)

        image_filename = _save_image(form.image.data, old_filename=None)

        petition = Petition(
            title=(form.title.data or "").strip(),
            description=(form.description.data or "").strip(),
            location=(form.location.data or "").strip(),
            latitude=lat,
            longitude=lng,
            image_filename=image_filename,
            user_id=current_user.id,
        )
        db.session.add(petition)
        db.session.commit()
        flash("Petizione creata con successo!", "success")
        return redirect(url_for("petitions.petition_detail", petition_id=petition.id))

    return render_template("pages/petition_form.html", form=form)

# =============================================================================
# Edit  ✅ NUOVO
# =============================================================================
@petitions_bp.route("/<int:petition_id>/edit", methods=["GET", "POST"])
@login_required
def edit_petition(petition_id):
    petition = Petition.query.get_or_404(petition_id)
    if petition.user_id != current_user.id:
        abort(403)

    form = PetitionForm(obj=petition)

    if form.validate_on_submit():
        # campi base
        petition.title = (form.title.data or "").strip()
        petition.description = (form.description.data or "").strip()
        petition.location = (form.location.data or "").strip()

        # coordinate
        lat = _parse_coord(form.latitude.data)
        lng = _parse_coord(form.longitude.data)
        if lat is None or lng is None:
            flash("Imposta correttamente la posizione sulla mappa.", "warning")
            return render_template("pages/petition_form.html", form=form, petition=petition)

        petition.latitude = lat
        petition.longitude = lng

        # immagine (facoltativa: se arriva una nuova, sostituisce la vecchia)
        petition.image_filename = _save_image(form.image.data, old_filename=petition.image_filename)

        db.session.commit()
        flash("Petizione aggiornata con successo!", "success")
        return redirect(url_for("petitions.petition_detail", petition_id=petition.id))

    return render_template("pages/petition_form.html", form=form, petition=petition)
    # NB: se preferisci separare il template, crea pages/petition_edit.html

# =============================================================================
# Detail
# =============================================================================
@petitions_bp.route("/<int:petition_id>")
@login_required
def petition_detail(petition_id):
    petition = Petition.query.get_or_404(petition_id)
    return render_template("pages/detail.html", item=petition, type="petition")

# =============================================================================
# Serve uploads (immagini petizioni)
# =============================================================================
@petitions_bp.route("/uploads/<path:filename>")
def petition_file(filename):
    return send_from_directory(PETITIONS_UPLOAD_FOLDER, filename)

# =============================================================================
# Sign
# =============================================================================
@petitions_bp.route("/<int:petition_id>/sign", methods=["POST"])
@login_required
def sign_petition(petition_id):
    petition = Petition.query.get_or_404(petition_id)
    already = PetitionSignature.query.filter_by(petition_id=petition.id, user_id=current_user.id).first()
    if already:
        flash("Hai già firmato questa petizione.", "warning")
    else:
        db.session.add(PetitionSignature(petition_id=petition.id, user_id=current_user.id))
        db.session.commit()
        flash("Hai firmato la petizione!", "success")
    return redirect(url_for("petitions.petition_detail", petition_id=petition.id))

# =============================================================================
# Support (associazioni)
# =============================================================================
@petitions_bp.route("/<int:petition_id>/support", methods=["POST"])
@login_required
def support_petition(petition_id):
    petition = Petition.query.get_or_404(petition_id)
    already = PetitionSupport.query.filter_by(petition_id=petition.id, association_id=current_user.id).first()
    if already:
        flash("Hai già sostenuto questa petizione.", "warning")
    else:
        db.session.add(PetitionSupport(petition_id=petition.id, association_id=current_user.id))
        db.session.commit()
        flash("Hai sostenuto la petizione!", "success")
    return redirect(url_for("petitions.petition_detail", petition_id=petition.id))


