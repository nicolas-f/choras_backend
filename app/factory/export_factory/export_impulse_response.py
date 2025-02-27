import io
import logging

from flask_smorest import abort
from virtualenv.config.convert import ListType

from app.models import Export
from app.models.Simulation import Simulation
from config import DefaultConfig, CustomExportParametersConfig as CustomExportParameters
import os

from app.factory.export_helper import ExportHelper
from app.factory.export_factory.export_strategy import ExportStrategy


# Create logger for this module
logger = logging.getLogger(__name__)

    
class ExportImpulseResponse(ExportStrategy):
    def export(self, export_type:str, params:ListType, simulationIds:ListType, zip_buffer:io.BytesIO)->io.BytesIO:

        for id in simulationIds:
            simulation: Simulation = Simulation.query.filter_by(id=id).first()
            export: Export = simulation.export
            xlsx_file_name: str = export.name
            wav_file_name = xlsx_file_name.split('.')[0] + ".wav"

            if not wav_file_name:
                logger.error("Impulse response .wav export with simulation is " + str(id) + "does not exists!")
                abort(400, message="Excel file doesn't exists!")

            if not xlsx_file_name:
                logger.error("Impulse response .csv export with simulation is " + str(id) + "does not exists!")
                abort(400, message="Excel file doesn't exists!")

            wav_file_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, wav_file_name)
            xlsx_file_path = os.path.join(DefaultConfig.UPLOAD_FOLDER_NAME, xlsx_file_name)

            helper = ExportHelper()


            try:
                if CustomExportParameters.value_wav_file in params:
                    zip_buffer = helper.write_file_to_zip_binary(zip_buffer, wav_file_path)
                if CustomExportParameters.value_csv_file in params:
                    zip_buffer = helper.extract_from_xlsx_to_csv_to_zip_binary(xlsx_file_path,
                                                                               {CustomExportParameters.impulse_response: CustomExportParameters.impulse_response_fs},
                                                                           zip_buffer, id)
            except Exception as e:
                logger.error("Error while writing wav or csv file to zip buffer: " + str(e))
                abort(400, message="Error while writing wav or csv file to zip buffer: " + str(e))

        return zip_buffer