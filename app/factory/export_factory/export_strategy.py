import logging
from abc import ABC, abstractmethod

from flask_smorest import abort
from virtualenv.config.convert import ListType

from app.models.Export import Export
from app.models.Simulation import Simulation
from config import DefaultConfig
import os
import io

import zipfile


# Create logger for this module
logger = logging.getLogger(__name__)


class ExportStrategy(ABC):
    @abstractmethod
    def export(self, export_type, params, simulationIds, zip_buffer):
        pass

class ExportExcel(ExportStrategy):
    def export(self, simulationIds:ListType, zip_buff:io.BytesIO) -> io.BytesIO:

        zip_buffer = zip_buff

        for id in simulationIds:
            simulation: Simulation = Simulation.query.filter_by(id=id).first()
            export: Export = simulation.export
            xlsx_file_name: str = export.name

            if not xlsx_file_name:
                logger.error("Export with simulation is " + str(id) + "does not exists!")
                abort(400, message="Excel file doesn't exists!")
        
    	
            xlsx_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, xlsx_file_name)
            xlsx_file_name = xlsx_file_name.split('.')[0] + '_simulation_' + str(id) + '.' + xlsx_file_name.split('.')[1]

            try:
                with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
                    # Save xlsx file to zip
                    zip_file.write(xlsx_path, arcname=xlsx_file_name)
            except Exception as e:
                logger.error("Error while writing excel file to zip buffer: " + str(e))
                abort(400, message="Error while writing excel file to zip buffer: " + str(e))

        return zip_buffer
    