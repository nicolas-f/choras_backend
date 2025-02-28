from flask.views import MethodView
from flask_smorest import Blueprint
from flask import send_from_directory, send_file

from app.schemas.export_schema import CustomExportSchema
from app.services import export_service

import logging

# Create Logger for this module
logger = logging.getLogger(__name__)


blp = Blueprint("Export", __name__, description="Export API")


@blp.route("/exports/<int:simulation_id>")
class ExportList(MethodView):
    @blp.response(200, content_type="application/zip")
    def get(self, simulation_id):
        zip_path = export_service.get_zip_path_by_sim_id(simulation_id)
        return send_from_directory(zip_path.parent, zip_path.name, as_attachment=True)
    
@blp.route("/exports/custom_export")
class CustomExport(MethodView):
    @blp.arguments(CustomExportSchema)
    @blp.response(200, content_type="application/zip")
    def post(self, body_data):
        zip_buffer = export_service.execute_export(body_data)
        zip_buffer.seek(0)  # Ensure buffer is at the start
        return send_file(zip_buffer, as_attachment=True, download_name="results.zip", mimetype="application/zip")
