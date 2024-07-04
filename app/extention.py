from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

migrate = Migrate(render_as_batch=True)
jwt = JWTManager()
cors = CORS()
