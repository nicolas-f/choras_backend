from flask_smorest import Api

from app.routes.user_router import blp as user_blueprint
from app.routes.material import blp as material_blueprint


# Register Blueprint
def register_routing(app):
    api = Api(app)
    api.register_blueprint(user_blueprint)
    api.register_blueprint(material_blueprint)
