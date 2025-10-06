from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

def _is_float(value: str) -> bool:
    if value is None: 
        return False
    try:
        float(value.replace(',', '.'))
        return True
    except (ValueError, AttributeError):
        return False

class PetitionForm(FlaskForm):
    title = StringField("Titolo", validators=[DataRequired(), Length(max=255)])
    description = TextAreaField("Descrizione", validators=[Optional(), Length(max=2000)])
    location = StringField("Luogo", validators=[Optional(), Length(max=255)])
    latitude = HiddenField("Latitudine", validators=[DataRequired(message="Seleziona un punto sulla mappa")])
    longitude = HiddenField("Longitudine", validators=[DataRequired(message="Seleziona un punto sulla mappa")])
    image = FileField("Immagine", validators=[Optional()])
    submit = SubmitField("Crea petizione")

    # validazione numerica
    def validate_latitude(self, field):
        if not _is_float(field.data):
            raise ValidationError("Latitudine non valida")

    def validate_longitude(self, field):
        if not _is_float(field.data):
            raise ValidationError("Longitudine non valida")
