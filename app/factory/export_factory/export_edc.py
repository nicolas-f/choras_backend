import io
import logging

from typing import List
from flask_smorest import abort

from app.models import Export
from app.models.Simulation import Simulation
from config import DefaultConfig
import os

from app.factory.export_factory.export_helper import ExportHelper
from app.factory.export_factory.strategy import ExportStrategy


# Create logger for this module
logger = logging.getLogger(__name__)


class ExportEdc(ExportStrategy):
    def export(self, export_type: str, params: List, simulationIds: List, zip_buffer: io.BytesIO) -> io.BytesIO:
        if params:
            for id in simulationIds:
                simulation: Simulation = Simulation.query.filter_by(id=id).first()
                export: Export = simulation.export
                xlsx_file_name: str = export.name

                if not xlsx_file_name:
                    logger.error("Plots export with simulation is " + str(id) + "does not exists!")
                    abort(400, message="Excel file doesn't exists!")

                xlsx_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, xlsx_file_name)
                try:
                    zip_buffer = ExportHelper.extract_from_xlsx_to_csv_to_zip_binary(
                        xlsx_path, {export_type: params}, zip_buffer, id
                    )
                except Exception as e:
                    logger.error("Error while writing energy decay curve(edc) csv file to zip buffer: " + str(e))
                    abort(400, message="Error while writing energy decay curve(edc) csv file to zip buffer: " + str(e))
        return zip_buffer
