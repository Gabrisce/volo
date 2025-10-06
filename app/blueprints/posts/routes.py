import os
from pathlib import Path
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort, send_from_directory, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.database.models.post import Post
from app.database.models.applause import Applause
from app.blueprints.posts.forms import PostForm
from app.database.models.notification import Notification


# 📌 Percorsi statici coerenti con gli altri blueprint (events, campaigns, reports)
BASE_DIR = Path(__file__).resolve().parent.parent  # app/blueprints
STATIC_FOLDER = BASE_DIR / "static"
POSTS_UPLOAD_FOLDER = STATIC_FOLDER / "uploads" / "posts"
POSTS_UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

posts_bp = Blueprint(
    "posts",
    __name__,
    url_prefix="/posts",
    template_folder="templates",
    static_folder=str(STATIC_FOLDER),
    static_url_path="/posts/static"
)

# 📌 Estensioni file consentite
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}

def allowed_file(filename: str) -> bool:
    """Controlla se l'estensione del file è tra quelle consentite."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------------------------------------------------------
# Creazione Post
# --------------------------------------------------------------------------
@posts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Creazione di un nuovo post con immagine e sondaggio opzionali."""
    if current_user.user_type != 'association':
        abort(403)

    form = PostForm()
    post = None

    if form.validate_on_submit():
        filename = None
        image_file = form.image.data

        if image_file and allowed_file(image_file.filename):
            raw_filename = secure_filename(image_file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{raw_filename}"
            save_path = POSTS_UPLOAD_FOLDER / filename
            image_file.save(str(save_path))

        # Creazione Post
        post = Post(
            title=form.title.data,
            content=form.content.data,
            image_filename=filename,
            association_id=current_user.id
        )
        db.session.add(post)
        db.session.flush()  # serve l'ID per legare eventuale sondaggio

        db.session.commit()
        flash("Post pubblicato con successo!", "success")
        return redirect(url_for("dashboard.dashboard_association"))

    return render_template("pages/post_form.html", form=form, post=post)

# --------------------------------------------------------------------------
# Modifica Post
# --------------------------------------------------------------------------
@posts_bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    """Modifica un post esistente e il suo sondaggio."""
    if current_user.user_type != "association":
        abort(403)

    post = Post.query.get_or_404(post_id)
    if post.association_id != current_user.id:
        abort(403)

    form = PostForm(obj=post)


    if form.validate_on_submit():
        # Aggiorna campi base
        post.title = form.title.data
        post.content = form.content.data

        # Gestione immagine
        if form.remove_image.data:
            if post.image_filename:
                try:
                    os.remove(POSTS_UPLOAD_FOLDER / post.image_filename)
                except OSError:
                    pass
            post.image_filename = None
        elif form.image.data and allowed_file(form.image.data.filename):
            raw_filename = secure_filename(form.image.data.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{raw_filename}"
            save_path = POSTS_UPLOAD_FOLDER / filename
            form.image.data.save(str(save_path))
            post.image_filename = filename


        post.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Post aggiornato con successo!", "success")
        return redirect(url_for("dashboard.dashboard_association"))

    return render_template("pages/post_form.html", form=form, post=post, edit=True)


# --------------------------------------------------------------------------
# Applausi (Mi piace)
# --------------------------------------------------------------------------
@posts_bp.route("/<int:post_id>/applause", methods=["POST"])
@login_required
def toggle_applause(post_id: int):
    post = Post.query.get_or_404(post_id)

    existing = Applause.query.filter_by(
        post_id=post.id, user_id=current_user.id
    ).first()

    if existing:
        # Rimuovo l’applauso
        db.session.delete(existing)

        # Rimuovo eventuale notifica associata a questo post e a questo utente
        notif = Notification.query.filter_by(
            user_id=post.association_id,
            post_id=post.id,
            type="post"
        ).first()
        if notif:
            db.session.delete(notif)

        db.session.commit()
        return jsonify({"status": "removed", "count": len(post.applause)})

    else:
        applause = Applause(post_id=post.id, user_id=current_user.id)
        db.session.add(applause)

        # Creo la notifica solo se l’utente che applaude non è l’associazione stessa
        if current_user.id != post.association_id:
            existing_notif = Notification.query.filter_by(
                user_id=post.association_id,
                post_id=post.id,
                type="post"
            ).first()
            if not existing_notif:
                notif = Notification(
                    user_id=post.association_id,
                    type="post",  # 👈 campo obbligatorio
                    message=f"{current_user.name} ha applaudito il tuo post: {post.title}",
                    post_id=post.id
                )
                db.session.add(notif)

        db.session.commit()
        return jsonify({"status": "added", "count": len(post.applause)})


# --------------------------------------------------------------------------
# Endpoint per servire i file upload dei post
# --------------------------------------------------------------------------
@posts_bp.route("/uploads/posts/<path:filename>")
def post_file(filename: str):
    """Serve i file caricati dentro uploads/posts"""
    return send_from_directory(POSTS_UPLOAD_FOLDER, filename)

# --------------------------------------------------------------------------
# Post detail (public)
# --------------------------------------------------------------------------
@posts_bp.route("/<int:post_id>", methods=["GET"])
def post_detail(post_id: int):
    """Dettaglio pubblico di un singolo post."""
    post = Post.query.get_or_404(post_id)
    return render_template("pages/post.html", post=post)

