import io
import logging

from flask_smorest import abort
from virtualenv.config.convert import ListType

from app.models.Simulation import Simulation
from app.models.Auralization import Auralization
from config import DefaultConfig, CustomExportParametersConfig as CustomExportParameters
import os

from app.factory.export_helper import ExportHelper
from app.factory.export_factory.export_strategy import ExportStrategy

# Create logger for this module
logger = logging.getLogger(__name__)


    
class ExportAuralization(ExportStrategy):
    def export(self, export_type:str, params:ListType, simulationIds:ListType, zip_buffer:io.BytesIO) -> io.BytesIO:

        for id in simulationIds:
            simulation: Simulation = Simulation.query.filter_by(id=id).first()
            auralization: Auralization = simulation.auralizations
            wav_file_name: str = auralization.wavFileName

            if not wav_file_name:
                logger.error("Auralization export with simulation is " + str(id) + "does not exists!")
                abort(400, message="Wav file doesn't exists!")


            wav_file_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, wav_file_name)
            helper = ExportHelper()

            try:
                if CustomExportParameters.value_wav_file in params:
                    zip_buffer = helper.write_file_to_zip_binary(zip_buffer, wav_file_path)
            except Exception as e:
                logger.error("Error while writing wav file to zip buffer: " + str(e))
                abort(400, message="Error while writing wav file to zip buffer: " + str(e))

        return zip_buffer