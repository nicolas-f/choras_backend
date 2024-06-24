from flask_smorest import Api

from app.routes.user_router import blp as user_blueprint
from app.routes.material import blp as material_blueprint
from app.routes.file import blp as file_blueprint
from app.routes.model import blp as model_blueprint
from app.routes.project import blp as project_blueprint


# Register Blueprint
def register_routing(app):
    api = Api(app)
    api.register_blueprint(user_blueprint)
    api.register_blueprint(material_blueprint)
    api.register_blueprint(file_blueprint)
    api.register_blueprint(model_blueprint)
    api.register_blueprint(project_blueprint)
