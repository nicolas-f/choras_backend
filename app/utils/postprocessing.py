from typing import Dict, List, Optional
import json
import pandas as pd
import logging

# Create Logger for this module
logger = logging.getLogger(__name__)


class ExcelExportHelper:
    def __init__(self, load_path: str, save_path: str) -> None:
        self.load_path = load_path
        self.save_path = save_path

    def export(self) -> bool:
        data: Optional[Dict] = self.__load_json__()
        if data is None:
            return False

        return self.__save_as_xlsx__(data)

    def __load_json__(self) -> Optional[Dict]:
        try:
            with open(self.load_path, 'r') as file:
                data: Dict = json.load(file)
        except FileNotFoundError as e:
            logger.error(f'File not found: {e}')
            return None

        return data

    def __save_as_xlsx__(self, data: Dict) -> bool:
        try:
            # TODO: Multiple sources and multiple receivers
            receiver_results: List[Dict[str, List[int]]] = data['results'][0]['responses'][0]['receiverResults']
            parameters: Dict[str, List[int]] = data['results'][0]['responses'][0]['parameters']

            parameter_sheet = pd.DataFrame(parameters)
            edc_sheet = pd.DataFrame()
            pressure_sheet = pd.DataFrame()

            # fill in edc_sheet and pressure_sheet
            time = receiver_results[0]['t']
            edc_sheet['t'] = time
            pressure_sheet['t'] = time
            for result in receiver_results:
                edc_sheet[str(result['frequency']) + 'Hz'] = result['data']
                pressure_sheet[str(result['frequency']) + 'Hz'] = result['data_pressure']

            with pd.ExcelWriter(self.save_path) as writer:
                parameter_sheet.to_excel(writer, sheet_name='Parameters', index=False)
                edc_sheet.to_excel(writer, sheet_name='EDC', index=False)
                pressure_sheet.to_excel(writer, sheet_name='Pressure', index=False)

        except Exception as e:
            logger.error(f'Error saving data to xlsx: {e}')
            return False

        return True
