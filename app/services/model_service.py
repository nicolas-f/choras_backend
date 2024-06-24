import logging
from flask_smorest import abort

from app.db import db
from app.models import Model

# Create logger for this module
logger = logging.getLogger(__name__)


def create_new_model(model_data):
    new_model = Model(
        name=model_data["name"],
        projectId=model_data["project"],
        sourceFileId=model_data["sourceFileId"],
        outputFileId=model_data["sourceFileId"]
    )

    try:
        db.session.add(new_model)
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not create a new model: {ex}")
        abort(400, message=f"Can not create a new model: {ex}")

    return new_model


def get_model(model_id):
    results = Model.query.filter_by(id=model_id).first()
    return results


def update_model(model_data, model_id):
    model = Model.query.filter_by(id=model_id).first()
    if not model:
        logger.error("Model doesn't exist, cannot update!")
        abort(400, message="Model doesn't exist, cannot update!")

    try:
        model.name = model_data["name"]
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not update! Error: {ex}")
        abort(400, message=f"Can not update! Error: {ex}")

    return model


def delete_model(model_id):
    result = Model.query.filter_by(id=model_id).delete()
    if not result:
        logger.error("Model doesn't exist, cannot delete!")
        abort(400, message="Model doesn't exist, cannot delete!")

    db.session.commit()
    return result
