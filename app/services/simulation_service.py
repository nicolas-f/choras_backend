import logging
from datetime import datetime
from flask_smorest import abort

from app.db import db
from app.models import Simulation, SimulationRun

# Create logger for this module
logger = logging.getLogger(__name__)


def create_new_simulation(simulation_data):
    new_simulation = Simulation(
        **simulation_data
    )

    try:
        db.session.add(new_simulation)
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not create a new model: {ex}")
        abort(400, message=f"Can not create a new model: {ex}")

    return new_simulation


def update_simulation_by_id(simulation_data, simulation_id):
    print('I came inside')
    simulation = get_simulation_by_id(simulation_id)
    if simulation is None:
        abort(400, 'Simulation not found')

    try:
        for key, value in simulation_data.items():
            setattr(simulation, key, value)

        simulation.updatedAt = datetime.now()
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not update the simulation: {ex}")
        abort(400, message=f"Can not update the simulation: {ex}")

    return simulation


def get_simulation_by_model_id(model_id):
    return Simulation.query.filter_by(
        modelId=model_id
    ).all()


def get_simulation_by_id(simulation_id):
    return Simulation.query.get(simulation_id)


def get_simulation_run():
    return SimulationRun.query.all()


def delete_model(model_id):
    result = Simulation.query.filter_by(id=model_id).delete()
    if not result:
        logger.error("Simulation doesn't exist, cannot delete!")
        abort(400, message="Simulation doesn't exist, cannot delete!")

    db.session.commit()
    return result
