import os

from flask import Flask
from pony.flask import Pony

from app.controllers import bp
from app.models import db


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "secret"
    app.config["instance_relative_config"] = True
    os.makedirs(app.instance_path, exist_ok=True)

    Pony(app)

    db.bind("sqlite", os.path.join(app.instance_path, "database.sqlite3"), create_db=True)
    db.generate_mapping(create_tables=True)

    app.register_blueprint(bp)

    return app
