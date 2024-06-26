from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.simulation_schema import (
    SimulationByModelQuerySchema,
    SimulationSchema,
    SimulationRunSchema
)
from app.services import simulation_service

blp = Blueprint("Simulation", __name__, description="Simulation API")


@blp.route("/simulations")
class SimulationList(MethodView):
    @blp.arguments(SimulationByModelQuerySchema, location='query')
    @blp.response(200, SimulationSchema(many=True))
    def get(self, query_data):
        result = simulation_service.get_simulation_by_model_id(
            query_data['modelId']
        )
        return result

    # @blp.arguments(SimulationCreateSchema, location='query')
    # @blp.response(200, SimulationSchema)
    # def post(self, query_data):
    #     result = model_service.create_new_model(query_data)
    #     return result


@blp.route("/simulations/run")
class SimulationRunList(MethodView):
    @blp.response(200, SimulationRunSchema(many=True))
    def get(self):
        result = simulation_service.get_simulation_run()
        return result
