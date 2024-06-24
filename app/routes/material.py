from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.material import MaterialSchema
from app.services import material_service

blp = Blueprint("Material", __name__, description="Material API")


@blp.route("/materials")
class MaterialList(MethodView):
    @blp.response(200, MaterialSchema(many=FutureWarning))
    def get(self):
        return material_service.get_all_materials()
