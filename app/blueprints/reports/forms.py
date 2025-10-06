from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

class ReportForm(FlaskForm):
    title = StringField("Titolo", validators=[DataRequired()])
    description = TextAreaField("Descrizione", validators=[DataRequired()])
    address = StringField("Indirizzo")
    latitude = HiddenField("Latitudine", validators=[DataRequired()])
    longitude = HiddenField("Longitudine", validators=[DataRequired()])
    image = FileField("Immagine", validators=[FileAllowed(["jpg", "jpeg", "png"], "Solo immagini")])
    submit = SubmitField("Invia segnalazione")