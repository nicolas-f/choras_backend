from flask.views import MethodView
from flask_smorest import Blueprint

from app.services import setting_service
from app.schemas.setting_schema import SettingSchema

blp = Blueprint("Setting", __name__, description="Simulation Settings API")


@blp.route("/simulation_settings/<string:simulation_type>")
class AudioFileList(MethodView):
    @blp.response(200)
    def get(self, simulation_type):
        setting_json = setting_service.get_setting_by_type(simulation_type)
        return setting_json


@blp.route("/simulation_settings")
class AudioFileList(MethodView):
    @blp.response(200, SettingSchema(many=True))
    def get(self):
        settings = setting_service.get_all_simulation_settings()
        return settings
