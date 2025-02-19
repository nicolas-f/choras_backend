from flask.views import MethodView
from flask_smorest import Blueprint
from flask import send_from_directory, send_file

from app.services import export_service

blp = Blueprint("Export", __name__, description="Export API")


# TODO: @almasmuhtadi @bbaigalmaa
@blp.route("/exports/<int:simulation_id>")
class ExportList(MethodView):
    @blp.response(200, content_type="application/zip")
    def get(self, simulation_id):
        zip_path = export_service.get_zip_path_by_sim_id(simulation_id)
        
        return send_from_directory(zip_path.parent, zip_path.name, as_attachment=True)

    # @blp.response(200, content_type="application/zip")
    # def post(self, request_body):
    #     zip_path = export_service.execute_export(request_body)

    #     return send_from_directory(zip_path.parent, zip_path.name, as_attachment=True)
