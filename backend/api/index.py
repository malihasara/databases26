import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
import auth
from db import close_db
from blueprints import admin, admin_portal, announcements, clubs, events, export, my_clubs, public


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=False)
    app.teardown_appcontext(close_db)

    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
        supports_credentials=True,
    )

    app.register_blueprint(auth.bp,          url_prefix="/api/auth")
    app.register_blueprint(my_clubs.bp,      url_prefix="/api/my-clubs")
    app.register_blueprint(clubs.bp,         url_prefix="/api/clubs")
    app.register_blueprint(events.bp,        url_prefix="/api/events")
    app.register_blueprint(admin.bp,         url_prefix="/api/admin/<club_id>")
    app.register_blueprint(announcements.bp, url_prefix="/api/admin/<club_id>/announcements")
    app.register_blueprint(public.bp,        url_prefix="/api/public")
    app.register_blueprint(admin_portal.bp,  url_prefix="/api/admin-portal")
    app.register_blueprint(export.bp,        url_prefix="/api/admin/<club_id>/export")

    @app.route("/api/health")
    def health():
        return jsonify(ok=True)

    return app


app = create_app()
