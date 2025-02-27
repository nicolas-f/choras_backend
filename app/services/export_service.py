import logging
import io
from flask_smorest import abort

from app.models.Export import Export
from app.models.Simulation import Simulation
from app.factory.export_factory import ExportFactory
from app.factory.export_factory import ExportExcel
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
    zip_buffer = io.BytesIO()
    exportFactory = ExportFactory()
    exportExcel = ExportExcel()

    simulationIds = export_dict[CustomExportParameters.key_simulationId]

    for key in CustomExportParameters.keys:
        params = export_dict[key]
        if params is None:
            abort(400, message=f"{key} is missing.")

        if key == CustomExportParameters.key_xlsx:
            param = bool(export_dict[key][0])
            if param:
                zip_buffer = exportExcel.export(simulationIds, zip_buffer)
        else:
            zip_buffer = exportFactory.get_exporter(key, params, simulationIds, zip_buffer)

    return zip_buffer


