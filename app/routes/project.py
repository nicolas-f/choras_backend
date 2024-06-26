from flask.views import MethodView
from flask_smorest import Blueprint

from app.schemas.project_schema import (
    ProjectCreateSchema, ProjectSchema, ProjectUpdateSchema, ProjectWithModelsSchema
)
from app.services import project_service

blp = Blueprint("Project", __name__, description="Project API")


@blp.route("/projects")
class ProjectList(MethodView):

    @blp.response(200, ProjectWithModelsSchema(many=True))
    def get(self):
        projects = project_service.get_all_projects()
        return projects

    @blp.arguments(ProjectCreateSchema)
    @blp.response(200, ProjectSchema)
    def post(self, body_data):
        result = project_service.create_new_project(body_data)
        return result


@blp.route("/projects/<int:project_id>")
class Project(MethodView):
    @blp.response(200, ProjectWithModelsSchema)
    def get(self, project_id):
        result = project_service.get_project(project_id)
        return result

    @blp.arguments(ProjectUpdateSchema)
    def put(self, project_body, project_id):
        result = project_service.update_project(project_body, project_id)
        return result

    @blp.response(200, ProjectSchema(many=True))
    def delete(self, project_id):
        result = project_service.delete_project(project_id)
        return result

# TODO: delete and update by group implementation comes here
