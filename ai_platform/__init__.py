"""AI Training Talent Platform — Flask application factory."""
from flask import Flask
from .extensions import db
from .models import JOB_CATEGORIES, SKILLS


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Configuration ──────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = "change-me-in-production"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ai_platform.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config:
        app.config.update(config)

    # ── Extensions ─────────────────────────────────────────────────────────
    db.init_app(app)

    # ── Blueprints ─────────────────────────────────────────────────────────
    from .routes.auth import auth_bp
    from .routes.professionals import professionals_bp
    from .routes.companies import companies_bp
    from .routes.jobs import jobs_bp
    from .routes.applications import applications_bp
    from .routes.frontend import frontend_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(professionals_bp, url_prefix="/api/professionals")
    app.register_blueprint(companies_bp, url_prefix="/api/companies")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(frontend_bp)

    # ── Inject constants into templates ────────────────────────────────────
    @app.context_processor
    def inject_constants():
        return {"JOB_CATEGORIES": JOB_CATEGORIES, "SKILLS": SKILLS}

    # ── Create tables ──────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app
