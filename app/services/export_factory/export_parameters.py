import logging
from abc import ABC, abstractmethod

from flask_smorest import abort
from app.models import Export
from app.services.export_service import ExportHelper
from config import DefaultConfig
import os


# Create logger for this module
logger = logging.getLogger(__name__)


class ExportStrategy(ABC):
    @abstractmethod
    def export(self, params, simulationId):
        pass

class ExportParameters(ExportStrategy):
    def export(self, params, simulationId):

        xlsx_file_name = Export.query.filter_by(simulationId=simulationId[0]).first().name

        if not xlsx_file_name:
            logger.error("Export with simulation is " + str(simulationId) + "does not exists!")
            abort(400, message="Excel file doesn't exists!")
        

        xlsx_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, xlsx_file_name)

        helper = ExportHelper()
        zip_binary = helper.extract_from_xlsx_to_csv_to_zip_binary(xlsx_path, {"Parameters": ["edt", "ts"]})
        
        
        # extract parameters from the excel
        # - check on parameters tab
        # - extract requested data into csv use helper tools
        # - temporarily store the data
        # param_dict = {"Parameters": params}
        return zip_binary