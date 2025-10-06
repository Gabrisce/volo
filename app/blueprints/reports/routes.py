# app/blueprints/reports/routes.py

import os
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.database.models.report import Report
from app.blueprints.reports.forms import ReportForm

# --------------------------------------------------------------------------
# Blueprint con cartella statica dedicata
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # .../app/blueprints
STATIC_FOLDER = BASE_DIR / "static"
REPORTS_UPLOAD_FOLDER = STATIC_FOLDER / "uploads" / "reports"
REPORTS_UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports",
    static_folder=str(STATIC_FOLDER),     # ✅ punto alla cartella /app/blueprints/static
    static_url_path="/reports/static"     # ✅ URL accessibile come /reports/static/...
)

# --------------------------------------------------------------------------
# Route per creare una segnalazione
# --------------------------------------------------------------------------
@reports_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_report():
    form = ReportForm()
    if form.validate_on_submit():
        image_file = form.image.data
        filename = None

        if image_file:
            raw_filename = secure_filename(image_file.filename)
            filename = raw_filename
            save_path = REPORTS_UPLOAD_FOLDER / filename
            image_file.save(str(save_path))

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
        # 👇 redirect diretto alla pagina unificata di dettaglio
        return redirect(url_for("public.detail", content_type="report", item_id=report.id))

    return render_template("pages/create_report.html", form=form)

# --------------------------------------------------------------------------
# Lista di tutte le segnalazioni
# --------------------------------------------------------------------------
@reports_bp.route("/list")
@login_required
def list_reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("pages/reports_list.html", reports=reports)

# --------------------------------------------------------------------------
# Dettaglio singola segnalazione → redirect alla detail unificata
# --------------------------------------------------------------------------
@reports_bp.route("/<int:report_id>")
@login_required
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    return redirect(url_for("public.detail", content_type="report", item_id=report.id))

# --------------------------------------------------------------------------
# Endpoint manuale per servire immagini reports
# --------------------------------------------------------------------------
@reports_bp.route("/uploads/<path:filename>")
def report_file(filename):
    """Serve i file caricati dentro uploads/reports"""
    return send_from_directory(REPORTS_UPLOAD_FOLDER, filename)

# --------------------------------------------------------------------------
# Elimina una segnalazione
# --------------------------------------------------------------------------
@reports_bp.route("/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        abort(403)

    db.session.delete(report)
    db.session.commit()
    flash("Segnalazione eliminata con successo.", "success")
    return redirect(url_for("dashboard.dashboard_volunteer"))

