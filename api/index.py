import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import Flask, g, redirect, url_for

from config import Config
import auth
from db import close_db
from blueprints import clubs, events, my_clubs


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.config.from_object(Config)
    app.teardown_appcontext(close_db)

    app.register_blueprint(auth.bp)
    app.register_blueprint(my_clubs.bp)
    app.register_blueprint(clubs.bp)
    app.register_blueprint(events.bp)

    @app.route("/")
    def index():
        if g.user:
            return redirect(url_for("my_clubs.index"))
        return redirect(url_for("auth.login"))

    return app


app = create_app()
