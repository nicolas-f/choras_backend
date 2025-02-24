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
from app.services.export_helper import ExportHelper
from app.services.export_factory.export_strategy import ExportExcel
from config import CustomExportParametersConfig as CustomExportParameters

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


def execute_export(export_dict):
# def execute_export(request_body):

    # request_body = '{ "SimulationId" : [1], 
    # "Parameters" : ["edt", "t20", "t30", "c80", "d50", "ts", "spl_t0_freq"],
    #  "EDC" : ["63Hz", "125Hz", "250Hz", "500Hz", "1000Hz", "2000Hz", "4000Hz", "8000Hz"], 
    # "Auralization" : ["Impulse response .wav", "Auralization output .wav", "Impulse response .csv"]}'
    # request_body = '{ "SimulationId" : [1], "Parameters" : ["edt", "t20", "t30", "c80", "d50", "ts", "spl_t0_freq"], "EDC" : ["125Hz", "250Hz", "500Hz", "1000Hz"], "Auralization" : ["Impulse response .wav", "Auralization output .wav", "Impulse response .csv"]}'
    # request_body = '{ "SimulationId" : [1], "Parameters" : [], "EDC" : ["125Hz", "250Hz", "500Hz", "1000Hz"], "Auralization" : ["Impulse response .wav", "Auralization output .wav", "Impulse response .csv"]}'
    # request_body = '{ "SimulationId" : [1, 2], "Parameters" : [], "EDC" : [], "Auralization" : ["Impulse response .wav", "Auralization output .wav", "Impulse response .csv"]}'
    # export_dict = json.loads(request_body) # export_dict["simulationId"] or export_dict["parameters"]


    # return export_request
    # simulation_ids: [1,2,3,4,5]
    # parse the request_body and collect the type and request into dict
    # export_request:
    #      K               Value
    # "parameters"       ["T20","SPL"] or if nil or [] assume all selected
    # "plots"           ["1000KHz,200KHz"]  or if nil or [] assume all selected

    print(export_dict)

    simulationIds = export_dict["SimulationId"]

    print("Simulation ids: ", simulationIds)

    parameters_values = list(export_dict[CustomExportParameters.key_parameter])
    edc_values = list(export_dict[CustomExportParameters.key_edc])
    auralization_values = list(export_dict[CustomExportParameters.key_auralization])

    parameters_all = list(["edt", "t20", "t30", "c80", "d50", "ts", "spl_t0_freq"])
    edc_all = list(["63Hz", "125Hz", "250Hz", "500Hz", "1000Hz", "2000Hz", "4000Hz", "8000Hz"])
    auralization_all = list(["WavImpulseResponse", "WavAuralization", "CsvImpulseResponse"])

    

    try:
        if not parameters_values:
            print("Parameters values are empty such that setting all values.")
            parameters_values = parameters_all
        if not edc_values:
            print("EDC values are empty such that setting all values.")
            edc_values = edc_all

    except Exception as e:
            logger.error(f'Error checking request body.')
            return None
    



    exportFactory = ExportFactory()
    exportExcel = ExportExcel()


    try:
        zip_buffer = io.BytesIO()

        zip_buffer = exportExcel.export(simulationIds, zip_buffer)
        zip_buffer = exportFactory.get_exporter(CustomExportParameters.key_parameter, parameters_values, simulationIds, zip_buffer)
        zip_buffer = exportFactory.get_exporter(CustomExportParameters.key_edc, edc_values, simulationIds, zip_buffer)

    except Exception as e:
            logger.error(f'Error when extrating zip: {e}')
            return None
    


    # For testing purpose
    # with open("test.zip", "wb") as f:
    #     f.write(zip_buffer.getvalue())

    # print("Done")
    

    

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

    return zip_buffer


