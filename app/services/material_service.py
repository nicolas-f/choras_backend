import logging
import json
from app.db import db
from sqlalchemy import asc
from flask_smorest import abort
from config import app_dir
from app.models import Material
import os

# Create logger for this module
logger = logging.getLogger(__name__)


def get_all_materials():
    return Material.query.order_by(
        asc(Material.id)
    ).all();


def insert_initial_materials():
    materials = get_all_materials()
    if len(materials):
        return
    logger.info("Inserting initial materials")
    with open(os.path.join(app_dir, 'models', 'data', 'materials.json')) as json_materials:
        initial_materials = json.load(json_materials)
        try:
            new_materials = []
            for material in initial_materials:
                new_materials.append(
                    Material(
                        name=material['name'],
                        description=material['description'],
                        category=material['category'],
                        materialJson=material['materialJson'],
                        materialMetadataJson=material['materialMetadataJson'],
                        defaultAbsorption=material['defaultAbsorption'],
                        defaultScattering=material['defaultScattering']
                    )
                )

            db.session.add_all(new_materials)
            db.session.commit()

        except Exception as ex:
            db.session.rollback()
            logger.error(f"Can not insert initial materials! Error: {ex}")
            abort(400, message=f"Can not insert initial materials! Error: {ex}")

    return {"message": "Initial materials added successfully!"}
