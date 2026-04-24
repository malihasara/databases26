import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import Flask, redirect, url_for

from config import Config
import auth
from db import close_db


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.config.from_object(Config)
    app.teardown_appcontext(close_db)

    app.register_blueprint(auth.bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app


app = create_app()
