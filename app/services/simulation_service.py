import logging
from flask_smorest import abort
from app.db import db
from app.models import Simulation, SimulationRun, Task
from app.services import model_service, mesh_service
from app.types import TaskType, Status
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime

from celery import shared_task

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
    simulation = get_simulation_by_id(simulation_id)

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
    ).order_by(Simulation.updatedAt.desc()).all()


def get_simulation_run():
    return SimulationRun.query.all()


def delete_simulation(simulation_id):
    try:
        Simulation.query.filter_by(
            id=simulation_id
        ).delete()
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Error deleting the simulation: {ex}")
        abort(500, message=f"Error deleting the simulation: {ex}")


def delete_simulation_run(simulation_run_id):
    try:
        SimulationRun.query.filter_by(
            id=simulation_run_id
        ).delete()
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Error deleting the previous simulation run: {ex}")
        abort(500, message=f"Error deleting the previous simulation run: {ex}")


def get_simulation_by_id(simulation_id):
    simulation = Simulation.query.filter_by(id=simulation_id).first()
    if not simulation:
        logger.error('Simulation with id ' + str(simulation_id) + 'does not exists!')
        abort(400, message="Simulation doesn't exists!")
    return simulation


def create_source_task(task_type, source_id):
    try:
        task = Task(
            taskType=task_type,
            status=Status.Created
        )
        db.session.add(task)
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Error creating the task: {ex}")
        abort(500, message=f"Error creating the task: {ex}")

    # Extract the public attributes of the SQLAlchemy object
    task_dict = {k: v for k, v in task.__dict__.items() if not k.startswith('_')}

    # Add additional attributes using dictionary unpacking
    task_dict.update({
        'percentage': 0,
        'sourcePointId': source_id
    })

    return task_dict


def start_solver_task(simulation_id):
    simulation = get_simulation_by_id(simulation_id)

    if simulation.simulationRunId:
        delete_simulation_run(simulation.simulationRunId)

    model = model_service.get_model(simulation.modelId)
    mesh = mesh_service.get_mesh_by_id(model.meshId)

    sources_tasks = []

    for source in simulation.sources:
        task_statuses = []
        if simulation.taskType.value in (TaskType.DE.value, TaskType.BOTH.value):
            task_statuses.append(
                create_source_task(TaskType.DE.value, source['id'])
            )
        if simulation.taskType.value in (TaskType.DG.value, TaskType.BOTH.value):
            task_statuses.append(
                create_source_task(TaskType.DG.value, source['id'])
            )
        sources_tasks.append({
            'label': source['label'],
            'orderNumber': source['orderNumber'],
            'percentage': 0,
            'sourcePointId': source['id'],
            'taskStatuses': task_statuses
        })

    new_simulation_run = SimulationRun(
        sources=sources_tasks,
        receivers=simulation.receivers,
        taskType=simulation.taskType,
        settingsPreset=simulation.settingsPreset,
        layerIdByMaterialId=simulation.layerIdByMaterialId,
        solverSettings=simulation.solverSettings,
        status=Status.Created
    )

    try:
        db.session.add(new_simulation_run)
        db.session.commit()

        simulation.simulationRunId = new_simulation_run.id
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not create a new simulation run: {ex}")
        abort(400, message=f"Can not create a new simulation run: {ex}")

    # TODO: start the solver task (call their function here)
    # for now i assume it is a function that runs it and update the simulation status
    # Run the background task asynchronously
    run_solver.delay(new_simulation_run.id)

    return new_simulation_run


@shared_task
def run_solver(simulation_run_id):
    from app.db import db
    from app.models import SimulationRun
    from app.types import Status
    import time
    import logging

    # Create logger for this module

    logger.info(f"Running solver task for simulation_run_id: {simulation_run_id}")

    try:
        # Scoped session factory to ensure proper session management
        session_factory = sessionmaker(bind=db.engine)
        session = scoped_session(session_factory)()  # Create a new session for this thread

        simulation_run = session.query(SimulationRun).get(simulation_run_id)
        if simulation_run is None:
            logger.error(f"SimulationRun with id {simulation_run_id} not found")
            return

        logger.info(f"SimulationRun found: {simulation_run}")
        simulation = session.query(Simulation).filter_by(
            simulationRunId=simulation_run.id
        ).first()

        time.sleep(5)  # Simulate processing
        simulation_run.status = Status.ProcessingResults
        if simulation:
            simulation.status = Status.ProcessingResults
        session.commit()
        logger.info(f"SimulationRun status updated to {simulation_run.status}")

        time.sleep(5)  # Simulate processing
        simulation_run.status = Status.Completed
        simulation_run.updatedAt = datetime.now()
        simulation_run.completedAt = datetime.now()
        if simulation:
            simulation.status = Status.Completed
            simulation.updatedAt = datetime.now()
            simulation.completedAt = datetime.now()
        session.commit()
        logger.info(f"SimulationRun status updated to {simulation_run.status}")

    except Exception as ex:
        session.rollback()
        logger.error(f"Cannot update simulation run: {ex}")

    finally:
        session.close()  # Ensure the session is closed after use
        logger.info(f"Session closed for simulation_run_id: {simulation_run_id}")
