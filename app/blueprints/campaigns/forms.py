from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, HiddenField, RadioField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError


class CampaignForm(FlaskForm):
    """Form per la creazione e modifica di campagne da parte delle associazioni."""

    # 📝 Titolo
    title = StringField(
        "Titolo della campagna",
        validators=[
            DataRequired(message="Il titolo è obbligatorio."),
            Length(max=255, message="Il titolo non può superare i 255 caratteri."),
        ],
        render_kw={"placeholder": "Es. Raccolta fondi per la mensa solidale"},
    )

    # ✏️ Descrizione
    description = TextAreaField(
        "Descrizione dettagliata",
        validators=[DataRequired(message="La descrizione è obbligatoria.")],
        render_kw={"placeholder": "Spiega gli obiettivi, le attività e l'impatto atteso"},
    )

    # ⏳ Durata: temporanea/perenne
    duration = RadioField(
        "Durata",
        choices=[("temporary", "Temporanea"), ("perennial", "Perenne")],
        default="temporary",
        validators=[DataRequired()],
    )

    # 🗓️ Data/ora inizio (sempre obbligatoria)
    date = DateTimeLocalField(
        "Data/ora inizio",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired(message="Indica una data/ora di inizio.")],
        render_kw={"placeholder": "YYYY-MM-DDTHH:MM"},
    )

    # 🗓️ Data/ora fine (obbligatoria solo se temporanea)
    end_date = DateTimeLocalField(
        "Data/ora fine",
        format="%Y-%m-%dT%H:%M",
        validators=[Optional()],
        render_kw={"placeholder": "YYYY-MM-DDTHH:MM"},
    )

    # 💰 Obiettivo economico (testuale ma validato)
    goal_amount = StringField(
        "Obiettivo economico (facoltativo)",
        validators=[
            Optional(),
            Length(max=255, message="Massimo 255 caratteri."),
            Regexp(
                r"^[0-9., €]*$",
                message="Inserisci solo numeri, punti, virgole o il simbolo €.",
            ),
        ],
        render_kw={"placeholder": "Es. 5000 €, oppure lascia vuoto"},
    )

    # 📍 Luogo (campo visibile)
    location = StringField(
        "Luogo (facoltativo)",
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "Es. Via Roma 12, Bari"},
    )

    # 🌍 Coordinate nascoste (riempite via JS da Google Maps)
    latitude = HiddenField()
    longitude = HiddenField()

    # 🖼️ Immagine (opzionale)
    image = FileField(
        "Immagine della campagna (JPG o PNG)",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png"], "Formato non supportato: usa JPG o PNG."),
        ],
    )

    # ✅ Submit
    submit = SubmitField("Pubblica campagna")

    # 🔎 Validazione form-level
    def validate(self, extra_validators=None) -> bool:
        ok = super().validate(extra_validators=extra_validators)
        if not ok:
            return False

        # Se temporanea: end_date obbligatoria e successiva a date
        if self.duration.data == "temporary":
            if not self.end_date.data:
                self.end_date.errors.append("Obbligatoria per campagne temporanee.")
                return False
            if self.date.data and self.end_date.data <= self.date.data:
                self.end_date.errors.append("La fine deve essere successiva all’inizio.")
                return False
        else:
            # Se perenne: ignora eventuale end_date compilata
            self.end_date.data = None

        return True
