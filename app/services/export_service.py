import json
import zipfile
import pandas as pd
import logging
import os
import io
from pathlib import Path
from flask_smorest import abort
from typing import Dict, List, Optional

import config
from app.models.Export import Export
from app.models.Simulation import Simulation

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


class ExportHelper:
    def parse_json_file_to_xlsx_file(self, json_path: str, xlsx_path: str) -> bool:
        """Convert simulation results to an Excel file"""
        data: Optional[Dict] = self.__load_json__(json_path)
        if data is None:
            return False

        return self.__parse_json_data_to_xlsx_file__(data, xlsx_path)

    def write_data_to_xlsx_file(self, xlsx_path: str, sheet: str, data: Dict, mode: str = 'a') -> bool:
        try:
            df = pd.DataFrame(data)
            with pd.ExcelWriter(xlsx_path, mode = mode) as writer:
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

    def write_file_to_zip_binary(self, zip_buffer: io.BytesIO, file_path: str, mode: str = 'a') -> Optional[io.BytesIO]:
        try:
            file_path: Path = Path(file_path)
            zip_file = zipfile.ZipFile(zip_buffer, mode = mode)
            zip_file.write(file_path, arcname=file_path.name)
            return zip_buffer

        except Exception as e:
            logger.error(f'Error saving file to zip: {e}')
            return None
        
    
    def extract_from_xlsx_to_dict(self, xlsx_path: str, sheets_columns: Dict[str, List[str]]) -> Optional[pd.DataFrame]:
        try:
            xlsx_path: Path = Path(xlsx_path)
            xlsx = pd.ExcelFile(xlsx_path)

            data: Dict[str, Dict[str, List]] = {}
            for sheet, columns in sheets_columns.items():
                df = pd.read_excel(xlsx, sheet_name=sheet)
                data[sheet] = {}
                for col in columns:
                    data[sheet][col] = df[col].tolist()

            return data

        except Exception as e:
            logger.error(f'Error extracting data from xlsx: {e}')
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
