from flask import Blueprint, render_template, abort
from flask.typing import ResponseReturnValue
from app import db
from app.database.models.user import User
from app.database.models.report import Report
from app.database.models.participation import Participation

# 📌 Blueprint per i Volontari
volunteers_bp = Blueprint("volunteers", __name__, url_prefix="/volunteers")


# 👤 Profilo pubblico del volontario
@volunteers_bp.route("/public/<int:volunteer_id>", endpoint="public_profile")
def public_profile(volunteer_id: int) -> ResponseReturnValue:
    """Mostra il profilo pubblico di un volontario con segnalazioni, partecipazioni ed associazioni seguite."""

    volunteer: User = User.query.get_or_404(volunteer_id)

    # ✅ Verifica che sia effettivamente un volontario
    if volunteer.user_type != "volunteer":
        abort(404)

    # 📊 Recupera le informazioni collegate
    reports: list[Report] = Report.query.filter_by(user_id=volunteer.id).all()
    participations: list[Participation] = Participation.query.filter_by(volunteer_id=volunteer.id).all()

    followed_count = len(volunteer.followed_associations.all())


    return render_template(
        "pages/volunteer_profile.html",
        volunteer=volunteer,
        reports=reports,
        participations=participations,
        followed_associations_count=followed_count,
    )
