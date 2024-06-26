import os

from flask import Flask

import manage
from app.blueprint import register_routing
from app.db import db
from app.extention import cors, migrate
from app.utils.logging import configure_logging

from sqlalchemy.engine import Engine
from sqlalchemy import event


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app(settings_module):
    app = Flask(__name__)
    app.config.from_object(settings_module)

    # Initialize the extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, supports_credentials="true", resources={r"*": {"origins": "*"}})
    manage.init_app(app)

    # Logging configuration
    configure_logging(app)

    # Register Blueprint
    register_routing(app)

    return app


app = create_app(
    os.getenv("APP_SETTINGS_MODULE")
)
