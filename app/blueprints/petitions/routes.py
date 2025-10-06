from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.database.models.petition import Petition, PetitionSignature, PetitionSupport
from app.blueprints.petitions.forms import PetitionForm

petitions_bp = Blueprint(
    "petitions",
    __name__,
    url_prefix="/petitions",
    static_folder="static",
    static_url_path="/petitions/static",
    template_folder="templates"
)

# ✅ Creazione
@petitions_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_petition():
    form = PetitionForm()
    if form.validate_on_submit():
        try:
            lat = float((form.latitude.data or "").replace(",", "."))
            lng = float((form.longitude.data or "").replace(",", "."))
        except ValueError:
            flash("Imposta la posizione sulla mappa.", "warning")
            return render_template("pages/petition_form.html", form=form)

        petition = Petition(
            title=form.title.data.strip(),
            description=(form.description.data or "").strip(),
            location=(form.location.data or "").strip(),
            latitude=lat,
            longitude=lng,
            image_filename=None,
            user_id=current_user.id
        )
        db.session.add(petition)
        db.session.commit()
        flash("Petizione creata con successo!", "success")
        return redirect(url_for("petitions.petition_detail", petition_id=petition.id))
    return render_template("pages/petition_form.html", form=form)


# ✅ Dettaglio
@petitions_bp.route("/<int:petition_id>")
@login_required
def petition_detail(petition_id):
    petition = Petition.query.get_or_404(petition_id)
    return render_template(
        "pages/detail.html",
        item=petition,
        type="petition"
    )

# ✅ Firma volontario
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

# ✅ Supporto associazione
@petitions_bp.route("/<int:petition_id>/support", methods=["POST"])
@login_required
def support_petition(petition_id):
    petition = Petition.query.get_or_404(petition_id)
    # Supponiamo che current_user.id sia ID associazione se è un'associazione
    already = PetitionSupport.query.filter_by(petition_id=petition.id, association_id=current_user.id).first()
    if already:
        flash("Hai già sostenuto questa petizione.", "warning")
    else:
        db.session.add(PetitionSupport(petition_id=petition.id, association_id=current_user.id))
        db.session.commit()
        flash("Hai sostenuto la petizione!", "success")
    return redirect(url_for("petitions.petition_detail", petition_id=petition.id))

@petitions_bp.route("/<int:petition_id>/delete", methods=["POST"])
@login_required
def delete_petition(petition_id):
    petition = Petition.query.get_or_404(petition_id)

    # Solo l’autore può eliminarla
    if petition.user_id != current_user.id:
        flash("Non sei autorizzato a eliminare questa petizione.", "danger")
        return redirect(url_for("dashboard.dashboard_volunteer"))

    db.session.delete(petition)
    db.session.commit()
    flash("Petizione eliminata con successo.", "success")
    return redirect(url_for("dashboard.dashboard_volunteer"))