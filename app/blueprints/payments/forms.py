from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange


class DonationForm(FlaskForm):
    full_name = StringField("Nome e Cognome", validators=[Length(max=150)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    amount = DecimalField("Importo", validators=[DataRequired(), NumberRange(min=1)])
    method = SelectField(
        "Metodo di pagamento",
        choices=[("stripe", "Carta di credito (Stripe)"), ("paypal", "PayPal")],
        validators=[DataRequired()],
    )
    message = TextAreaField("Messaggio", validators=[Length(max=500)])
    submit = SubmitField("Dona ora")
