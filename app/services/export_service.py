import json
import zipfile
import pandas as pd
import logging
import os
import io
from pathlib import Path
from flask_smorest import abort
from typing import Dict, List, Optional

from app.models.Export import Export
from app.models.Simulation import Simulation
from app.services.export_factory.factory import ExportFactory

# Create Logger for this module
logger = logging.getLogger(__name__)


def get_zip_path_by_sim_id(simulation_id: int) -> io.BytesIO:
    simulation: Simulation = Simulation.query.filter_by(id=simulation_id).first()
    if simulation is None:
        abort(404, message="No simulation found with this id.")

    export: Export = simulation.export
    if export is None:
        abort(404, message="No export found for this simulation.")

    try:
        # TODO: @almasmuhtadi @bbaigalmaa
        ...
    except Exception as ex:
        abort(400, message=f"Error while getting the zip file path: {ex}")
        return None


#http://localhost:3000/custom_export
def execute_export():
# def execute_export(request_body):

    request_body = '{ "SimulationId" : [1], "Parameters" : ["edt", "t20", "t30", "c80", "d50", "ts", "spl_t0_freq"], "EDC" : ["63Hz", "125Hz", "250Hz", "500Hz", "1kHz", "2kHz", "4kHz", "8kHz"], "Auralization" : ["Impulse response .wav", "Auralization output .wav", "Impulse response .csv"]}'
    export_dict = json.loads(request_body) # export_dict["simulationId"] or export_dict["parameters"]


    # return export_request
    # simulation_ids: [1,2,3,4,5]
    # parse the request_body and collect the type and request into dict
    # export_request:
    #      K               Value
    # "parameters"       ["T20","SPL"] or if nil or [] assume all selected
    # "plots"           ["1000KHz,200KHz"]  or if nil or [] assume all selected

    export_factory = ExportFactory()
    keys = list(export_dict.keys())
    
    simulationId = export_dict["SimulationId"]
    key_parameter = "Parameters"
    # key_plot = "EDC"
    # key_auralization = "Auralization"

    param_zip_binary = export_factory.get_exporter(key_parameter, list(export_dict[key_parameter]), simulationId)
    # export_factory.get_exporter("plot")
    # export_factory.get_exporter("auralization")

    # check if export_request contain define exporttype in key -> parameters, plots, auralization call get_export_types

    

    # throw error if none valid

    # zip_buffer = io.BytesIO()

    # with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
    #     for resource_type in selected_resources:
    #         strategy = ExportFactory.get_exporter(resource_type)
    #         if strategy:
    #             file_names = strategy.export({})
    #             iteratively
    #             write
    #             to
    #             zip
    #             zip_file.writestr(file_name, f"Dummy content of {file_name}")

    # zip_buffer.seek(0)

    # cleanup the files

    # return zip file



class ExportHelper:
    def parse_json_file_to_xlsx_file(self, json_path: str, xlsx_path: str) -> bool:
        """Convert simulation results to an Excel file"""
        data: Optional[Dict] = self.__load_json__(json_path)
        if data is None:
            return False

        return self.__parse_json_data_to_xlsx_file__(data, xlsx_path)

    def write_data_to_xlsx_file(self, xlsx_path: str, sheet: str, data: Dict) -> bool:
        try:
            df = pd.DataFrame(data)
            with pd.ExcelWriter(xlsx_path) as writer:
                df.to_excel(writer, sheet_name=sheet, index=False)
            return True

        except Exception as e:
            logger.error(f'Error adding data to xlsx: {e}')
            return False

    def extract_from_xlsx_to_csv_to_zip_binary(
        self, xlsx_path: str, sheets_columns: Dict[str, List[str]]
    ) -> Optional[io.BytesIO]:
        try:
            xlsx_path: Path = Path(xlsx_path)
            xlsx = pd.ExcelFile(xlsx_path)

            # Create a BytesIO object
            zip_buffer = io.BytesIO()
            csv_buffer = io.StringIO()

            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                # Save xlsx file to zip
                zip_file.write(xlsx_path, arcname=xlsx_path.name)

                # Convert selected sheets and columns to csv and save them to zip
                for sheet, columns in sheets_columns.items():
                    df = pd.read_excel(xlsx, sheet_name=sheet)
                    for col in columns:
                        df[[col]].to_csv(csv_buffer, header=False, index=False)
                        csv_buffer.seek(0)
                        zip_file.writestr(f'{sheet}_{col}.csv', csv_buffer.getvalue())
                        csv_buffer.truncate(0)

                csv_buffer.close()

            return zip_buffer

        except Exception as e:
            logger.error(f'Error saving data to csv: {e}')
            return None

    def write_file_to_zip_binary(self, zip_buffer: io.BytesIO, file_path: str) -> Optional[io.BytesIO]:
        try:
            file_path: Path = Path(file_path)
            zip_file = zipfile.ZipFile(zip_buffer, 'a')
            zip_file.write(file_path, arcname=file_path.name)
            return zip_buffer

        except Exception as e:
            logger.error(f'Error saving file to zip: {e}')
            return None

    def __load_json__(self, json_path) -> Optional[Dict]:
        try:
            with open(json_path, 'r') as file:
                data: Dict = json.load(file)
        except FileNotFoundError as e:
            logger.error(f'File not found: {e}')
            return None

        return data

    def __parse_json_data_to_xlsx_file__(self, data: Dict, xlsx_path: str) -> bool:
        try:
            # TODO: Multiple sources and multiple receivers
            receiver_results: List[Dict[str, List[int]]] = data['results'][0]['responses'][0]['receiverResults']
            parameters: Dict[str, List[int]] = data['results'][0]['responses'][0]['parameters']

            parameter_sheet = pd.DataFrame(parameters)
            edc_sheet = pd.DataFrame()

            # fill in edc_sheet and pressure_sheet
            time = receiver_results[0]['t']
            edc_sheet['t'] = time
            for result in receiver_results:
                edc_sheet[str(result['frequency']) + 'Hz'] = result['data']

            with pd.ExcelWriter(xlsx_path) as writer:
                parameter_sheet.to_excel(writer, sheet_name='Parameters', index=False)
                edc_sheet.to_excel(writer, sheet_name='EDC', index=False)

        except Exception as e:
            logger.error(f'Error saving data to xlsx: {e}')
            return False

        return True
