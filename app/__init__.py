import os

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine

import config
import manage
from app.blueprint import register_routing
from app.db import db
from app.extention import cors, migrate
from app.job_queue import make_celery  # Import the Celery setup
from app.utils.logging import configure_logging

# Load environment variables from a .env file
load_dotenv()


# @event.listens_for(Engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     """
#     Return a list of random ingredients as strings.

#     :param kind: Optional "kind" of ingredients.
#     :type kind: list[str] or None
#     :raise lumache.InvalidKindError: If the kind is invalid.
#     :return: The ingredients list.
#     :rtype: list[str]

#     """
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA foreign_keys=ON")
#     cursor.close()


def create_app(settings_module=None):
    local_app = Flask(os.getenv("APP_NAME"))
    if settings_module==None:
        settings_module = config.LocalConfig
    local_app.config.from_object(settings_module)
    print("APP_NAME " + str(os.getenv("APP_NAME")));
    print("SQLALCHEMY_DATABASE_URI " + settings_module.SQLALCHEMY_DATABASE_URI);
    # Initialize the extensions
    db.init_app(local_app)

    local_celery = make_celery(local_app)
    local_celery.set_default()

    migrate.init_app(local_app, db)
    cors.init_app(
        local_app, supports_credentials="true", resources={r"*": {"origins": "*"}}
    )
    manage.init_app(local_app)

    # Logging configuration
    configure_logging(local_app)

    # Register Blueprint
    register_routing(local_app)

    return local_app, local_celery


app, celery = create_app()

app.app_context().push()
