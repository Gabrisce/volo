from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from app.database.models.user import User
from app.blueprints.auth.forms import LoginForm, VolunteerRegisterForm, AssociationRegisterForm

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ------------------- LOGIN -------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            flash("Login effettuato con successo.", "success")
            return redirect(url_for("dashboard.dashboard"))
        flash("Email o password non validi.", "danger")

    return render_template("pages/login.html", form=form)


# ------------------- LOGOUT -------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout effettuato.", "info")
    return redirect(url_for("auth.login"))


# ------------------- REGISTRAZIONE VOLONTARIO -------------------
@auth_bp.route("/register/volunteer", methods=["GET", "POST"])
def register_volunteer():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = VolunteerRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Questa email è già registrata.", "warning")
            return render_template("pages/register_volunteer.html", form=form)

        # Normalizza i dati geografici
        lat = form.latitude.data or None
        lon = form.longitude.data or None
        try:
            lat = float(lat) if lat not in (None, "") else None
            lon = float(lon) if lon not in (None, "") else None
        except ValueError:
            lat, lon = None, None

        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            password=generate_password_hash(form.password.data),
            user_type="volunteer",
            date_of_birth=form.date_of_birth.data,
            phone=form.phone.data or None,
            latitude=lat,
            longitude=lon,
            bio=form.bio.data or None,
            disponibilita=form.disponibilita.data or None,
        )
        db.session.add(user)
        db.session.commit()
        flash("Registrazione completata! Ora effettua il login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("pages/register_volunteer.html", form=form)


# ------------------- REGISTRAZIONE ASSOCIAZIONE -------------------
@auth_bp.route("/register/association", methods=["GET", "POST"])
def register_association():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    form = AssociationRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Questa email è già registrata.", "warning")
            return render_template("pages/register_association.html", form=form)

        # Normalizza i dati geografici
        lat = form.latitude.data or None
        lon = form.longitude.data or None
        try:
            lat = float(lat) if lat not in (None, "") else None
            lon = float(lon) if lon not in (None, "") else None
        except ValueError:
            lat, lon = None, None

        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            password=generate_password_hash(form.password.data),
            user_type="association",
            address=form.address.data or None,
            latitude=lat,
            longitude=lon,
            bio=form.bio.data or None,
            website=form.website.data or None,
            iban=form.iban.data or None,
        )
        db.session.add(user)
        db.session.commit()
        flash("Registrazione completata! Ora effettua il login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("pages/register_association.html", form=form)


# ------------------- RESET PASSWORD -------------------
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    email = request.form.get("email")
    if not email:
        flash("Inserisci un indirizzo email valido.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        flash("Nessun account trovato con questa email.", "danger")
        return redirect(url_for("auth.login"))

    # TODO: invio email con token sicuro
    flash("Se l'email è registrata, riceverai un link per reimpostare la password.", "info")
    return redirect(url_for("auth.login"))
