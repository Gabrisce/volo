import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.blueprints.campaigns.forms import CampaignForm
from app.database.models.campaign import Campaign

campaigns_bp = Blueprint(
    "campaigns",
    __name__,
    url_prefix="/campaigns",
    template_folder="templates",
    static_folder="../static"   # 👈 punta a app/blueprints/static
)

UPLOAD_FOLDER = Path(campaigns_bp.static_folder) / "uploads" / "campaigns"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# ✅ Crea nuova campagna
@campaigns_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_campaign():
    if current_user.user_type != "association":
        abort(403)

    form = CampaignForm()
    if form.validate_on_submit():
        # ── Upload immagine (opzionale)
        image_file = form.image.data
        filename = None
        if image_file:
            raw_filename = secure_filename(image_file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{raw_filename}"
            image_path = UPLOAD_FOLDER / filename
            image_file.save(str(image_path))

        # ── Geolocalizzazione (opzionale)
        lat = request.form.get("latitude")
        lng = request.form.get("longitude")

        # ── Costruzione oggetto Campaign
        # Regola: se perenne → end_date = None (il Form già la azzera in validate())
        campaign = Campaign(
            title=form.title.data,
            description=form.description.data,
            goal_amount=form.goal_amount.data or None,
            location=form.location.data or None,
            latitude=float(lat) if lat else None,
            longitude=float(lng) if lng else None,
            image_filename=filename,
            association_id=current_user.id,
            # campi temporali/durata
            duration=form.duration.data,      # "temporary" | "perennial"
            date=form.date.data,              # inizio (obbligatoria)
            end_date=form.end_date.data,      # fine (solo se temporary)
        )

        db.session.add(campaign)
        db.session.commit()
        flash("Campagna creata con successo!", "success")
        return redirect(url_for("dashboard.dashboard_association"))

    return render_template("pages/campaign_form.html", form=form)


# 👁️ Elenco campagne dell'associazione loggata
@campaigns_bp.route("/my")
@login_required
def my_campaigns():
    if current_user.user_type != "association":
        abort(403)

    my_campaigns = (
        Campaign.query.filter_by(association_id=current_user.id)
        .order_by(Campaign.created_at.desc())
        .all()
    )
    return render_template("pages/my_campaigns.html", campaigns=my_campaigns)


# ✏️ Modifica campagna esistente
@campaigns_bp.route("/edit/<int:campaign_id>", methods=["GET", "POST"])
@login_required
def edit_campaign(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)

    if current_user.user_type != "association" or campaign.association_id != current_user.id:
        abort(403)

    form = CampaignForm(obj=campaign)

    if form.validate_on_submit():
        # Geolocalizzazione (opzionale)
        lat = request.form.get("latitude")
        lng = request.form.get("longitude")

        # Upload immagine (opzionale)
        image_file = form.image.data
        if image_file:
            raw_filename = secure_filename(image_file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{raw_filename}"
            image_path = UPLOAD_FOLDER / filename
            image_file.save(str(image_path))
            campaign.image_filename = filename

        # Aggiorna i campi dal form
        campaign.title = form.title.data
        campaign.description = form.description.data
        campaign.goal_amount = form.goal_amount.data or None
        campaign.location = form.location.data or None
        campaign.duration = form.duration.data
        campaign.date = form.date.data
        campaign.end_date = form.end_date.data  # il form l’ha messa None se perenne

        # Geo
        campaign.latitude = float(lat) if lat else campaign.latitude
        campaign.longitude = float(lng) if lng else campaign.longitude

        db.session.commit()
        flash("Campagna aggiornata con successo!", "success")
        return redirect(url_for("campaigns.my_campaigns"))

    return render_template("pages/campaign_form.html", form=form, edit=True, campaign=campaign)


# 📄 Dettaglio campagna
@campaigns_bp.route("/<int:campaign_id>")
@login_required
def campaign_detail(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template("pages/detail.html", item=campaign, type="campaign")


# 🗑️ Elimina campagna
@campaigns_bp.route("/<int:campaign_id>/delete", methods=["POST"])
@login_required
def delete_campaign(campaign_id: int):
    campaign = Campaign.query.get_or_404(campaign_id)

    if campaign.association_id != current_user.id:
        abort(403)

    db.session.delete(campaign)
    db.session.commit()
    flash("Campagna eliminata con successo", "success")
    return redirect(url_for("dashboard.dashboard_association"))
