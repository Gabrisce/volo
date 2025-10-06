import os
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, session, flash, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.database.models.user import User
from app.blueprints.dashboard.forms import ProfileForm  # eventualmente spostalo in forms/settings.py

# --- Costanti ---
SUPPORTED_LANGS = ["it", "en", "es", "fr", "uk", "ru", "ar"]

# --- Blueprints ---
settings_bp = Blueprint(
    "settings",
    __name__,
    url_prefix="/settings",
    template_folder="templates",
    static_folder="../static"
)

lang_bp = Blueprint("lang", __name__, url_prefix="/lang")

# ----------------------------------------------------------------------
# SEZIONE SETTINGS
# ----------------------------------------------------------------------

@settings_bp.route("/")
@login_required
def index():
    """Pagina principale impostazioni."""
    return render_template("settings/index.html")


@settings_bp.route("/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    """
    Pagina modifica profilo (volontario/associazione).
    Gestisce nome, bio, età, foto profilo.
    """
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Aggiorna i dati base
        current_user.name = form.name.data
        current_user.bio = form.bio.data
        if hasattr(current_user, "age"):
            current_user.age = form.age.data

        # Upload immagine profilo
        if form.photo.data:
            filename = secure_filename(form.photo.data.filename)
            upload_folder = os.path.join(
                current_app.root_path, "blueprints", "static", "uploads", "profile-photo"
            )
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            form.photo.data.save(file_path)
            current_user.photo_filename = filename

        db.session.commit()
        flash("Profilo aggiornato con successo!", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("settings/edit_profile.html", form=form)


@settings_bp.route("/preferences")
@login_required
def preferences():
    """Pagina preferenze (tema, lingua, ecc.)."""
    return render_template("settings/preferences.html")


@settings_bp.route("/notifications")
@login_required
def notifications():
    """Pagina notifiche."""
    return render_template("settings/notifications.html")


@settings_bp.route("/security")
@login_required
def security():
    """Pagina sicurezza (password, SPID/CIE, ecc.)."""
    return render_template("settings/security.html")

# ----------------------------------------------------------------------
# SEZIONE LINGUE
# ----------------------------------------------------------------------

@lang_bp.route("/set/<lang_code>")
def set_language(lang_code):
    """Imposta la lingua dell’interfaccia."""
    if lang_code not in SUPPORTED_LANGS:
        flash("Lingua non supportata", "warning")
        return redirect(request.referrer or url_for("home.home"))

    session["lang"] = lang_code
    flash("Lingua aggiornata!", "success")
    return redirect(request.referrer or url_for("home.home"))
