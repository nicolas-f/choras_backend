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


def execute_export():
# def execute_export(request_body):

    # request_body = '{ "SimulationId" : [1], "Parameters" : ["edt", "t20", "t30", "c80", "d50", "ts", "spl_t0_freq"], "EDC" : ["63Hz", "125Hz", "250Hz", "500Hz", "1000Hz", "2000Hz", "4000Hz", "8000Hz"], "Auralization" : ["Impulse response .wav", "Auralization output .wav", "Impulse response .csv"]}'
    request_body = '{ "SimulationId" : [1], "Parameters" : ["edt", "t20", "t30", "c80", "d50", "ts", "spl_t0_freq"], "EDC" : ["125Hz", "250Hz", "500Hz", "1000Hz"], "Auralization" : ["Impulse response .wav", "Auralization output .wav", "Impulse response .csv"]}'
    export_dict = json.loads(request_body) # export_dict["simulationId"] or export_dict["parameters"]


    # return export_request
    # simulation_ids: [1,2,3,4,5]
    # parse the request_body and collect the type and request into dict
    # export_request:
    #      K               Value
    # "parameters"       ["T20","SPL"] or if nil or [] assume all selected
    # "plots"           ["1000KHz,200KHz"]  or if nil or [] assume all selected

    simulationId = export_dict["SimulationId"]
    key_parameter = "Parameters"
    key_plot = "EDC"
    key_auralization = "Auralization"

    parameters_values = list(export_dict[key_parameter])
    edc_values = list(export_dict[key_plot])
    auralization_values = list(export_dict[key_auralization])

    # try:
        # check values are empty or is this have an values

    # except Exception as e:
    #         logger.error(f'Error saving file to zip: {e}')
    #         return None


    exportFactory = ExportFactory()
    exportExcel = ExportExcel()

    zip_buffer = io.BytesIO()

    excel_zip_binary = exportExcel.export(simulationId[0], zip_buffer)
    parameters_zip_binary = exportFactory.get_exporter(key_parameter, parameters_values, simulationId[0], excel_zip_binary)
    plots_zip_binary = exportFactory.get_exporter(key_plot, edc_values, simulationId[0], parameters_zip_binary)


    
    # with open("test.zip", "wb") as f:
    #     f.write(plots_zip_binary.getvalue())

    # parameters_zip_binary.close()
    # print("Done")
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


