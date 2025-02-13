from flask_smorest import abort
from typing import Optional
from pathlib import Path

import config
from app.models.Export import Export
from app.models.Simulation import Simulation


def get_zip_path_by_sim_id(simulation_id: int) -> Optional[Path]:
    simulation: Simulation = Simulation.query.filter_by(id=simulation_id).first()
    if simulation is None:
        abort(404, message="No simulation found with this id.")

    export: Export = simulation.export
    if export is None:
        abort(404, message="No export found for this simulation.")

    try:
        zipfile_path = config.DefaultConfig.UPLOAD_FOLDER + '\\' + export.zipFileName
        return Path(zipfile_path)
    except Exception as ex:
        abort(400, message=f"Error while getting the zip file path: {ex}")
        return None
