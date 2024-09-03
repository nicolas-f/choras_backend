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
    local_app = Flask(os.getenv('APP_NAME'))
    local_app.config.from_object(settings_module)
    # Initialize the extensions
    db.init_app(local_app)

    local_celery = make_celery(local_app)
    local_celery.set_default()

    migrate.init_app(local_app, db)
    cors.init_app(local_app, supports_credentials="true", resources={r"*": {"origins": "*"}})
    manage.init_app(local_app)

    # Logging configuration
    configure_logging(local_app)

    # Register Blueprint
    register_routing(local_app)

    return local_app, local_celery


app, celery = create_app(
    os.getenv("APP_SETTINGS_MODULE")
)

app.app_context().push()
