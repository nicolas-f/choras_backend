from flask.views import MethodView
from flask_smorest import Blueprint
from flask_smorest import abort

from app.schemas.file import FileSchema, FileCreateSchema
from app.services import file_service

blp = Blueprint("File", __name__, description="File API")


@blp.route("/files")
class FileList(MethodView):
    @blp.response(200, FileSchema(many=True))
    def get(self):
        return file_service.get_slot()

    @blp.arguments(FileCreateSchema)
    def post(self, file_data):
        if 'file' not in file_data:
            abort(404, "No file provided!")

        result = file_service.create_file(file_data)
        return result

    @blp.arguments(FileCreateSchema)
    def delete(self, file_data):
        result = file_service.consume(file_data.slot)
        return result


@blp.route("/files/<int:file_id>")
class User(MethodView):
    @blp.response(200, FileSchema(many=True))
    def get(self, file_id):
        result = file_service.get_file_url(file_id)
        return result
