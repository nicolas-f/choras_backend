import logging
from flask_smorest import abort

from app.db import db
from app.models import Simulation

# Create logger for this module
logger = logging.getLogger(__name__)


def create_new_model(model_data):
    new_model = Simulation(
        name=model_data["name"],
        projectId=model_data["projectId"],
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


def get_simulation_by_model_id(model_id):
    return Simulation.query.filter_by(
        modelId=model_id
    ).all()


def get_simulation_run():
    return Simulation.query.all()


def update_model(model_id, model_data):
    model = Simulation.query.filter_by(id=model_id).first()
    if not model:
        logger.error("Simulation doesn't exist, cannot update!")
        abort(400, message="Simulation doesn't exist, cannot update!")

    try:
        model.name = model_data["name"]
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not update! Error: {ex}")
        abort(400, message=f"Can not update! Error: {ex}")

    return model


def delete_model(model_id):
    result = Simulation.query.filter_by(id=model_id).delete()
    if not result:
        logger.error("Simulation doesn't exist, cannot delete!")
        abort(400, message="Simulation doesn't exist, cannot delete!")

    db.session.commit()
    return result
