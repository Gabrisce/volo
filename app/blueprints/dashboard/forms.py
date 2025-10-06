from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, FileField, SubmitField
from wtforms.validators import Optional, Length, NumberRange

class ProfileForm(FlaskForm):
    name = StringField("Nome", validators=[Length(min=2, max=100)])
    age = IntegerField("Età", validators=[Optional(), NumberRange(min=1, max=120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=500)])
    photo = FileField("Foto profilo (JPG/PNG)", validators=[Optional()])
    submit = SubmitField("Salva modifiche")
