import logging
from abc import ABC, abstractmethod

from flask_smorest import abort
from app.models import Export
from config import DefaultConfig
import os
import io

import zipfile


# Create logger for this module
logger = logging.getLogger(__name__)


class ExportStrategy(ABC):
    @abstractmethod
    def export(self, export_type, params, simulationId, zip_buffer):
        pass

class ExportExcel(ExportStrategy):
    def export(self, simulationId, zip_buff):

        xlsx_file_name = Export.query.filter_by(simulationId=simulationId).first().name

        if not xlsx_file_name:
            logger.error("Export with simulation is " + str(simulationId) + "does not exists!")
            abort(400, message="Excel file doesn't exists!")
        

        xlsx_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, xlsx_file_name)

        zip_buffer = zip_buff

        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # Save xlsx file to zip
            zip_file.write(xlsx_path, arcname=xlsx_file_name)

        return zip_buffer
    