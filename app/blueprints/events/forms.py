# app/blueprints/events/forms.py

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    DateTimeField,
    SubmitField,
    HiddenField,
    RadioField,
    IntegerField,
)
from wtforms.validators import (
    DataRequired,
    Optional,
    NumberRange,
    Length,
    ValidationError,
)

# Limite superiore ragionevole per la capienza
MAX_CAPACITY = 100_000


class EventForm(FlaskForm):
    """Form per creare o modificare un evento."""

    # 📝 Titolo
    title = StringField(
        "Titolo evento",
        validators=[
            DataRequired(message="Inserisci un titolo."),
            Length(max=200, message="Il titolo può avere al massimo 200 caratteri."),
        ],
    )

    # ✏️ Descrizione
    description = TextAreaField(
        "Descrizione",
        validators=[
            DataRequired(message="Inserisci una descrizione."),
            Length(
                max=5000,
                message="La descrizione può avere al massimo 5000 caratteri.",
            ),
        ],
    )

    # 📅 Data e ora (HTML datetime-local -> %Y-%m-%dT%H:%M)
    date = DateTimeField(
        "Data e ora",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired(message="Inserisci una data valida.")],
    )

    # 📍 Luogo (testuale)
    location = StringField(
        "Luogo",
        validators=[
            DataRequired(message="Inserisci un luogo valido."),
            Length(max=255, message="Il luogo può avere al massimo 255 caratteri."),
        ],
    )

    # 👥 Capienza
    capacity_mode = RadioField(
        "Capienza",
        choices=[("unlimited", "Illimitata"), ("limited", "Limitata")],
        default="unlimited",
        validators=[DataRequired()],
    )

    capacity_max = IntegerField(
        "Numero massimo",
        validators=[
            Optional(),
            NumberRange(
                min=1,
                max=MAX_CAPACITY,
                message=f"Inserisci un numero valido (1–{MAX_CAPACITY}).",
            ),
        ],
    )

    # 🖼️ Immagine evento (opzionale)
    image = FileField(
        "Immagine evento (opzionale)",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png"], "Sono ammessi solo file JPG o PNG."),
        ],
    )

    # 🧭 Coordinate geografiche (invisibili nel form)
    latitude = HiddenField(validators=[Optional()])
    longitude = HiddenField(validators=[Optional()])

    # ✅ Submit
    submit = SubmitField("Salva evento")

    # ---- Validazioni personalizzate / normalizzazione ----

    def validate(self, **kwargs) -> bool:
        """Richiede capacity_max quando la capienza è limitata e normalizza i dati."""
        ok = super().validate(**kwargs)
        if not ok:
            return False

        if self.capacity_mode.data == "limited":
            # Deve essere presente e valido (NumberRange copre min/max)
            if self.capacity_max.data is None:
                self.capacity_max.errors.append(
                    "Indica il numero massimo di partecipanti."
                )
                return False
        else:
            # Normalizza: se illimitato, non consideriamo capacity_max
            self.capacity_max.data = None

        return True
