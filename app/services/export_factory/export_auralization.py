import logging
from abc import ABC, abstractmethod

from flask_smorest import abort
from app.models import Export
from app.models.Simulation import Simulation
from config import DefaultConfig
import os

from app.services.export_helper import ExportHelper
from app.services.export_factory.export_strategy import ExportStrategy


# Create logger for this module
logger = logging.getLogger(__name__)


    
class ExportAuralization(ExportStrategy):
    def export(self, export_type, params, simulationId):
        simulation: Simulation = Simulation.query.filter_by(id=simulationId).first()
        print("simulation", simulation)

        export: Export = simulation.export
        print("export", export)

        xlsx_file_name: str = export.name
        print("xlsx_file_name", xlsx_file_name)

        # xlsx_file_name = Export.query.filter_by(simulationId=simulationId).first().name

        if not xlsx_file_name:
            logger.error("Auralization export with simulation is " + str(simulationId) + "does not exists!")
            abort(400, message="Excel file doesn't exists!")
        

        xlsx_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, xlsx_file_name)
        helper = ExportHelper()
        zip_binary = helper.extract_from_xlsx_to_csv_to_zip_binary(xlsx_path, {export_type : params})
    

        return zip_binary