import os
from flask import Flask, render_template, redirect, url_for, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_babel import Babel

# Carica variabili da .env
load_dotenv()

# Estensioni create a livello modulo
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()

def create_app():
    # instance_relative_config=True => app.instance_path = <proj>/instance
    app = Flask(__name__, instance_relative_config=True)

    # Assicura che la cartella instance esista
    os.makedirs(app.instance_path, exist_ok=True)

    # Path assoluto al DB dentro instance/
    db_path = os.path.join(app.instance_path, "volo.db")

    # Config base
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", f"sqlite:///{db_path}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY"),
        STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY"),
    )

    # Inizializza estensioni
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Modelli (import dopo db.init_app)
    from app.database.models.user import User

    # User loader
    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    # --- Locale selector (Flask-Babel 4.x) ---
    def select_locale():
        return session.get("lang") or request.accept_languages.best_match(
            ["it", "en", "es", "fr", "uk", "ru", "ar"]
        ) or "it"

    babel.init_app(app, locale_selector=select_locale)

    # Blueprint
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.dashboard.routes import dashboard_bp
    from app.blueprints.home.routes import home_bp
    from app.blueprints.events.routes import events_bp
    from app.blueprints.posts.routes import posts_bp
    from app.blueprints.associations.routes import associations_bp
    from app.blueprints.campaigns.routes import campaigns_bp
    from app.blueprints.public.routes import public_bp
    from app.blueprints.reports.routes import reports_bp
    from app.blueprints.payments import payments_bp  
    from app.blueprints.full_map.routes import full_map_bp
    from app.blueprints.chat.routes import chat_bp
    from app.blueprints.volunteers.routes import volunteers_bp
    from app.blueprints.notifications.routes import notifications_bp
    from app.blueprints.settings.routes import settings_bp, lang_bp
    from app.blueprints.petitions.routes import petitions_bp


    # Registrazione blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(associations_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(public_bp, url_prefix="/public")
    app.register_blueprint(reports_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(full_map_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(volunteers_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(lang_bp)
    app.register_blueprint(petitions_bp)


    # Homepage
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard"))
        return render_template("pages/login.html")

    return app
