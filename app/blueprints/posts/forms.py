from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, FieldList
from wtforms.validators import DataRequired, Length, Optional


class PostForm(FlaskForm):
    """Form per creare o modificare un post, con immagine opzionale e sondaggio."""

    # 📝 Titolo del post
    title = StringField(
        "Titolo",
        validators=[
            DataRequired(message="Il titolo è obbligatorio."),
            Length(max=255, message="Massimo 255 caratteri."),
        ],
    )

    # ✏️ Contenuto del post
    content = TextAreaField(
        "Contenuto",
        validators=[DataRequired(message="Il contenuto non può essere vuoto.")],
    )

    # 📷 Immagine opzionale
    image = FileField(
        "Immagine del post (opzionale)",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "gif"],
                "Sono consentite solo immagini JPG, JPEG, PNG o GIF.",
            ),
        ],
    )

    # 🗑️ Spunta per rimuovere l'immagine esistente
    remove_image = BooleanField("Rimuovi immagine", default=False)

    # ✅ Pulsante invio
    submit = SubmitField("Pubblica")
