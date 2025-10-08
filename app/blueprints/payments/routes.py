# app/blueprints/payments/routes.py
from pathlib import Path
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import os
from app.database.models.user import User

from flask import (
    render_template, redirect, request, url_for, flash,
    send_from_directory, abort
)
from app import db
from app.database.models import Campaign, Donation
from app.utils.pdf_generator import generate_receipt
from . import payments_bp

# 👇 NEW
from flask_login import current_user  # <— ci serve per legare la donazione al volontario

import stripe

# -----------------------------------------------------------------------------
# Stripe config
# -----------------------------------------------------------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # usa sk_test_... in sandbox

# -----------------------------------------------------------------------------
# Percorso ricevute (statico dedicato)
# -----------------------------------------------------------------------------
# app/blueprints/static/download/receipts
BASE_DIR = Path(__file__).resolve().parent.parent  # → app/blueprints
RECEIPTS_FOLDER = BASE_DIR / "static" / "download" / "receipts"
RECEIPTS_FOLDER.mkdir(parents=True, exist_ok=True)



@payments_bp.route("/donation/<int:campaign_id>")
def donation_form(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template("pages/donation_form.html", campaign=campaign)


@payments_bp.route("/donation/<int:campaign_id>/create", methods=["POST"])
def create_donation(campaign_id):
    if not stripe.api_key:
        flash("Configurazione pagamento non completa (chiave Stripe mancante).", "danger")
        return redirect(url_for("payments.donation_form", campaign_id=campaign_id))

    campaign = Campaign.query.get_or_404(campaign_id)

    full_name = (request.form.get("full_name") or "").strip()
    email = (request.form.get("email") or "").strip()
    message = (request.form.get("message") or "").strip()
    method = "card"  # con Checkout paghiamo con carta
    raw_amount = (request.form.get("amount") or "").replace(",", ".").strip()

    # Validazione importo (Decimal + quantize a 2 decimali)
    try:
        amount_decimal = Decimal(raw_amount)
        if amount_decimal <= 0:
            raise InvalidOperation()
        amount_decimal = amount_decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        flash("Importo non valido. Inserisci un numero maggiore di zero.", "warning")
        return redirect(url_for("payments.donation_form", campaign_id=campaign_id))

    amount_cents = int((amount_decimal * 100).to_integral_value(rounding=ROUND_HALF_UP))

    try:
        # Crea Checkout Session con importo dinamico
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],  # esplicito, ok in Checkout
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"Donazione – {campaign.title}",
                    },
                    "unit_amount": amount_cents,  # centesimi interi
                },
                "quantity": 1,
            }],
            customer_email=email or None,
            metadata={
                "campaign_id": str(campaign.id),
                "full_name": full_name,
                "email": email,
                "amount": str(amount_decimal),  # lo riprendiamo alla success
                "method": method,
                "message": message,
            },
            success_url=url_for("payments.success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("payments.error", _external=True),
        )
    except stripe.error.StripeError as e:
        # Messaggio user-friendly in caso di errore Stripe
        flash("Impossibile avviare il pagamento. Riprova più tardi.", "danger")
        # Se vuoi loggare: current_app.logger.exception(e)
        return redirect(url_for("payments.donation_form", campaign_id=campaign_id))

    # Redirect 303 a Stripe
    return redirect(session.url, code=303)


@payments_bp.route("/donation/success")
def success():
    """
    Ritorno da Stripe con ?session_id=cs_...
    - Verifica pagamento completato
    - Crea Donation
    - Genera PDF ricevuta
    - Mostra link di download
    """
    session_id = request.args.get("session_id")
    if not session_id:
        abort(400, description="session_id mancante")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        flash("Errore nel recupero dei dati di pagamento.", "danger")
        return redirect(url_for("payments.error"))

    if session.get("payment_status") != "paid":
        flash("Pagamento non completato.", "warning")
        return redirect(url_for("payments.error"))

    md = session.get("metadata", {}) or {}
    campaign_id = int(md.get("campaign_id", "0") or 0)
    campaign = Campaign.query.get_or_404(campaign_id)

    # 👇 NEW: amount come float coerente con il modello (Float)
    try:
        amount_value = float(md.get("amount") or 0)
    except (TypeError, ValueError):
        amount_value = 0.0

  

       # 🔗 user_id: prima il login, poi fallback su email del metadata
    user_id_val = None
    if getattr(current_user, "is_authenticated", False):
        user_id_val = current_user.id
    elif md.get("email"):
        u = User.query.filter_by(email=md.get("email")).first()
        if u:
            user_id_val = u.id

    # Crea Donation (MVP: non idempotente; valuta di salvare session_id se vuoi evitare duplicati)
    donation = Donation(
        campaign_id=campaign.id,
        email=md.get("email"),
        full_name=md.get("full_name"),
        amount=amount_value,                # <— ora è float
        method=(md.get("method") or "card"),
        message=md.get("message"),
        user_id=user_id_val,                # <— QUI il collegamento al volontario
    )
    db.session.add(donation)
    db.session.commit()

    # Genera ricevuta direttamente in app/blueprints/static/download/receipts
    filename = generate_receipt(donation, campaign)
    donation.pdf_filename = filename
    db.session.commit()

    # URL alla route di download (NON static globale)
    receipt_url = url_for("payments.download_receipt", filename=donation.pdf_filename)

    related_events = campaign.related_events[:3]  # max 3 suggerimenti

    return render_template("pages/donation_success.html", donation=donation, receipt_url=receipt_url, related_events=related_events)


@payments_bp.route("/donation/error")
def error():
    return render_template("pages/donation_error.html")


# -----------------------------------------------------------------------------
# Download ricevuta (file statico dedicato, NON nello static globale app/)
# -----------------------------------------------------------------------------
@payments_bp.route("/receipt/<path:filename>")
def download_receipt(filename: str):
    if not filename:
        abort(404)
    return send_from_directory(
        RECEIPTS_FOLDER,
        filename,
        as_attachment=False,          # True se vuoi forzare il download
        download_name=filename
    )
