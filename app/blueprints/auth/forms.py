from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, SubmitField, TextAreaField,
    BooleanField, DateField, HiddenField
)
from wtforms.validators import DataRequired, InputRequired, Email, Length, EqualTo, Optional, Regexp


# 🔑 Login
class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[InputRequired(), Email(message="Inserisci un'email valida")]
    )
    password = PasswordField(
        "Password",
        validators=[InputRequired()]
    )
    submit = SubmitField("Login")


# 🏢 Registrazione Associazioni
class AssociationRegisterForm(FlaskForm):
    # 📌 DATI OBBLIGATORI
    name = StringField(
        "Denominazione",
        validators=[DataRequired(), Length(min=2, max=150, message="Inserisci la denominazione completa")]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(message="Inserisci un'email valida")]
    )
    phone = StringField(
        "Telefono referente",
        validators=[DataRequired(), Regexp(r"^\+?\d{6,20}$", message="Inserisci un numero valido con prefisso internazionale")]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6, message="La password deve avere almeno 6 caratteri")]
    )
    confirm_password = PasswordField(
        "Conferma Password",
        validators=[DataRequired(), EqualTo("password", message="Le password devono coincidere")]
    )

    # 📌 Sede legale → usiamo HiddenField per lat/lon (JS geocoding da indirizzo)
    address = StringField(
        "Sede legale (indirizzo completo)",
        validators=[DataRequired(), Length(max=255)]
    )
    latitude = HiddenField("Latitudine")
    longitude = HiddenField("Longitudine")

    # 📎 Upload documenti ufficiali
    official_docs = FileField(
        "Carica documenti ufficiali (es. Statuto, Visura Camerale)",
        validators=[DataRequired(), FileAllowed(["pdf", "jpg", "jpeg", "png"], "Formato non valido (solo PDF o immagini)")]
    )

    # 📌 FACOLTATIVI
    logo = FileField(
        "Logo / Immagine profilo",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Solo immagini JPG/PNG")]
    )
    bio = TextAreaField(
        "Descrizione / Bio",
        validators=[Optional(), Length(max=500, message="Massimo 500 caratteri")]
    )
    website = StringField(
        "Sito web o link social",
        validators=[Optional(), Length(max=255)]
    )
    iban = StringField(
        "IBAN per accrediti",
        validators=[Optional(), Regexp(r"^[A-Z0-9]{15,34}$", message="Inserisci un IBAN valido")]
    )

    # ✅ CONSENSI OBBLIGATORI
    consenso_dati = BooleanField(
        "Acconsento al trattamento dei dati personali (GDPR)",
        validators=[DataRequired(message="Devi acconsentire al trattamento dei dati")]
    )
    accetta_termini = BooleanField(
        "Accetto Termini e Condizioni e l’Informativa Privacy",
        validators=[DataRequired(message="Devi accettare i Termini e Condizioni")]
    )

    submit = SubmitField("Registrati come Associazione")



# 👤 Registrazione Volontari
class VolunteerRegisterForm(FlaskForm):
    # 📌 Dati obbligatori
    name = StringField(
        "Nome e cognome",
        validators=[DataRequired(), Length(min=2, max=150, message="Inserisci nome e cognome validi")]
    )
    date_of_birth = DateField(
        "Data di nascita",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Inserisci la data di nascita")],
        render_kw={"type": "date"}  # HTML5 date picker
    )
    phone = StringField(
        "Numero di telefono",
        validators=[
            DataRequired(),
            Regexp(r"^\+?\d{6,20}$", message="Inserisci un numero valido con prefisso internazionale")
        ]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(message="Inserisci un'email valida")]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6, message="La password deve avere almeno 6 caratteri")]
    )
    confirm_password = PasswordField(
        "Conferma Password",
        validators=[DataRequired(), EqualTo("password", message="Le password devono coincidere")]
    )

    # 🌍 Geolocalizzazione (JS)
    latitude = HiddenField("Latitudine")
    longitude = HiddenField("Longitudine")

    # 🖼️ Facoltativi
    photo = FileField(
        "Foto profilo",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Solo immagini JPG/PNG")]
    )
    bio = TextAreaField(
        "Breve bio",
        validators=[Optional(), Length(max=500, message="Massimo 500 caratteri")]
    )
    disponibilita = TextAreaField(
        "Disponibilità (giorni/orari preferiti)",
        validators=[Optional(), Length(max=255, message="Massimo 255 caratteri")]
    )

    # ✅ Consensi obbligatori
    consenso_dati = BooleanField(
        "Acconsento al trattamento dei dati personali (GDPR)",
        validators=[InputRequired(message="Devi acconsentire al trattamento dei dati")]
    )
    accetta_termini = BooleanField(
        "Accetto Termini e Condizioni e l’Informativa Privacy",
        validators=[InputRequired(message="Devi accettare i Termini e Condizioni")]
    )

    submit = SubmitField("Registrati come Volontario")
