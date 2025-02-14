from typing import Dict

from flask.views import MethodView
from flask_smorest import Blueprint

from app.services import auralization_service
from app.schemas.auralization_schema import AudioFileSchema

blp = Blueprint("Auralization", __name__, description="Auralization API")


@blp.route("/auralizations/aduiofiles")
class AudioFileList(MethodView):
    @blp.response(200, AudioFileSchema(many=True))
    def get(self):
        audio_files = auralization_service.get_all_audio_files()
        return audio_files