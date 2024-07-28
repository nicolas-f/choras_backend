from marshmallow import Schema, fields
from app.schemas.model_schema import ModelSchema
from app.schemas.simulation_schema import SimulationSchema
from app.models import Project


class ProjectSchema(Schema):
    id = fields.Number()
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    group = fields.Str(required=True)
    createdAt = fields.Str()
    updatedAt = fields.Str()


class ProjectWithModelsSchema(ProjectSchema):
    models = fields.List(fields.Nested(ModelSchema))


class ProjectCreateSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    group = fields.Str(required=True)


class ProjectUpdateSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str()


class ProjectUpdateByGroupQuerySchema(Schema):
    group = fields.Str(required=True)


class ProjectUpdateByGroupBodySchema(Schema):
    newGroup = fields.Str(required=True)


class ProjectSimulationsSchema(Schema):
    modelName = fields.Str(required=True)
    modelId = fields.Integer(required=True)
    simulations = fields.List(fields.Nested(SimulationSchema))
    modelCreatedAt = fields.String(required=True)
    projectId = fields.Integer(required=True)
    projectName = fields.String(required=True)
    group = fields.Str(required=True)
