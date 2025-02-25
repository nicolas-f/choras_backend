from flask.views import MethodView
from flask_smorest import Blueprint

from app.services import setting_service

blp = Blueprint("Setting", __name__, description="Simulation Settings API")


@blp.route("/simulation_settings/<string:simulation_type>")
class AudioFileList(MethodView):
    @blp.response(200)
    def get(self, simulation_type):
        setting_json = setting_service.get_setting_by_type(simulation_type)
        return setting_json


# TODO: frontend requests for all simulation methods and display them on UI, rather than hardcoding
