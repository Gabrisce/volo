# app/blueprints/reports/routes.py

import os
import time
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.database.models.report import Report
from app.blueprints.reports.forms import ReportForm

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

BASE_DIR = Path(__file__).resolve().parent.parent  # .../app/blueprints
STATIC_FOLDER = BASE_DIR / "static"
REPORTS_UPLOAD_FOLDER = STATIC_FOLDER / "uploads" / "reports"
REPORTS_UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports",
    static_folder=str(STATIC_FOLDER),     # ✅ /app/blueprints/static
    static_url_path="/reports/static"     # ✅ URL: /reports/static/...
)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS

def _unique_name(original: str) -> str:
    base = secure_filename(original)
    # timestamp per evitare collisioni
    stem, dot, ext = base.partition(".")
    return f"{current_user.id}_{int(time.time())}_{stem}.{ext}" if dot else f"{current_user.id}_{int(time.time())}_{base}"

def _save_image(file_storage, old_filename: str | None = None) -> str | None:
    """
    Salva una nuova immagine (se fornita) e opzionalmente elimina il file precedente.
    Ritorna il nuovo filename relativo.
    """
    if not file_storage or not getattr(file_storage, "filename", ""):
        return old_filename

    if not _allowed(file_storage.filename):
        flash("Formato immagine non valido. Usa jpg, jpeg, png o webp.", "danger")
        return old_filename

    # elimina vecchio file se presente
    if old_filename:
        try:
            (REPORTS_UPLOAD_FOLDER / old_filename).unlink(missing_ok=True)
        except Exception:
            pass

    new_name = _unique_name(file_storage.filename)
    save_path = REPORTS_UPLOAD_FOLDER / new_name
    file_storage.save(str(save_path))
    return new_name

# --------------------------------------------------------------------------
# Crea
# --------------------------------------------------------------------------
@reports_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_report():
    form = ReportForm()
    if form.validate_on_submit():
        filename = _save_image(form.image.data, old_filename=None)

        report = Report(
            title=form.title.data,
            description=form.description.data,
            address=form.address.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            image_filename=filename,
            user_id=current_user.id
        )
        db.session.add(report)
        db.session.commit()
        flash("Segnalazione inviata con successo!", "success")
        return redirect(url_for("public.detail", content_type="report", item_id=report.id))

    return render_template("pages/create_report.html", form=form)

# --------------------------------------------------------------------------
# Modifica  ✅ NUOVO
# --------------------------------------------------------------------------
@reports_bp.route("/<int:report_id>/edit", methods=["GET", "POST"])
@login_required
def edit_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        abort(403)

    form = ReportForm(obj=report)

    if form.validate_on_submit():
        # aggiorna campi testuali
        report.title = form.title.data
        report.description = form.description.data
        report.address = form.address.data
        report.latitude = form.latitude.data
        report.longitude = form.longitude.data

        # eventuale nuova immagine (sostituisce la precedente)
        report.image_filename = _save_image(form.image.data, old_filename=report.image_filename)

        db.session.commit()
        flash("Segnalazione aggiornata con successo!", "success")
        return redirect(url_for("public.detail", content_type="report", item_id=report.id))

    return render_template("pages/create_report.html", form=form, report=report)
    # Nota: se preferisci riusare lo stesso template del create, usa "pages/create_report.html"

# --------------------------------------------------------------------------
# Lista
# --------------------------------------------------------------------------
@reports_bp.route("/list")
@login_required
def list_reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("pages/reports_list.html", reports=reports)

# --------------------------------------------------------------------------
# Dettaglio → redirect alla detail unificata
# --------------------------------------------------------------------------
@reports_bp.route("/<int:report_id>")
@login_required
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    return redirect(url_for("public.detail", content_type="report", item_id=report.id))

# --------------------------------------------------------------------------
# Serve immagini caricate
# --------------------------------------------------------------------------
@reports_bp.route("/uploads/<path:filename>")
def report_file(filename):
    return send_from_directory(REPORTS_UPLOAD_FOLDER, filename)

# --------------------------------------------------------------------------
