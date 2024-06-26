import logging
from flask_smorest import abort
from app.db import db
from app.models import Project
from sqlalchemy import asc

# Create logger for this module
logger = logging.getLogger(__name__)


def get_all_projects():
    return Project.query.order_by(asc(Project.createdAt)).all()


def create_new_project(project_data):
    new_project = Project(
        name=project_data["name"],
        group=project_data["group"].strip(),
        description=project_data["description"]
    )

    try:
        db.session.add(new_project)
        db.session.commit()

    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not create a new project: {ex}")
        abort(400, message=f"Can not create a new project: {ex}")

    return new_project


def get_project(project_id):
    results = Project.query.filter_by(id=project_id).first()
    return results


def update_project(project_id, project_data):
    project = Project.query.filter_by(id=project_id).first()
    if not project:
        logger.error("Project doesn't exist, cannot update!")
        abort(400, message="Project doesn't exist, cannot update!")

    try:
        project.name = project_data["name"]
        project.description = project_data["description"]
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not update! Error: {ex}")
        abort(400, message=f"Can not update! Error: {ex}")

    return project


def delete_project(project_id):
    result = Project.query.filter_by(id=project_id)
    if not result:
        logger.error("Project doesn't exist, cannot delete!")
        abort(400, message="Project doesn't exist, cannot delete!")
    result.delete()
    db.session.commit()
    return result


def delete_project_by_group(group):
    result = Project.query.filter_by(group=group).delete()
    if not result:
        logger.error("Group doesn't exist, cannot delete!")
        abort(400, message="Group doesn't exist, cannot delete!")

    db.session.commit()
    return result


def update_project_by_group(group, new_group):
    result = Project.query.filter_by(group=group).all()

    print(result)

    try:
        for project in result:
            project.group = new_group.strip()

        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        logger.error(f"Can not update! Error: {ex}")
        abort(400, message=f"Can not update! Error: {ex}")

    return result


def project_simulations(project_id):
    pass  # TODO
