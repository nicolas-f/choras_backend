import os
from flask import Flask
from dotenv import load_dotenv

import manage
from app.blueprint import register_routing
from app.db import db
from app.extention import cors, migrate
from app.utils.logging import configure_logging

from sqlalchemy.engine import Engine
from sqlalchemy import event
import config
from app.job_queue import make_celery  # Import the Celery setup

# Load environment variables from a .env file
load_dotenv()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app(settings_module):
    app = Flask(os.getenv('APP_NAME'))
    app.config.from_object(settings_module)
    # Initialize the extensions
    db.init_app(app)

    celery = make_celery(app)
    celery.set_default()

    migrate.init_app(app, db)
    cors.init_app(app, supports_credentials="true", resources={r"*": {"origins": "*"}})
    manage.init_app(app)

    # Logging configuration
    configure_logging(app)

    # Register Blueprint
    register_routing(app)

    return app, celery


app, celery = create_app(
    os.getenv("APP_SETTINGS_MODULE")
)

app.app_context().push()
