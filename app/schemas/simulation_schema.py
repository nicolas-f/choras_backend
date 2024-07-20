from marshmallow import Schema, fields, post_load, EXCLUDE
from app.types import TaskType, Status, Setting
from app.schemas.model_schema import ModelInfoBasicSchema


class SolverSettingsSchema(Schema):
    dgSettings = fields.Dict()
    deSettings = fields.Dict()


class SimulationCreateBodySchema(Schema):
    modelId = fields.Integer(required=True)
    name = fields.String(required=True)
    description = fields.String(required=False)
    layerIdByMaterialId = fields.Dict()
    solverSettings = fields.Nested(SolverSettingsSchema)


class SimulationSchema(SimulationCreateBodySchema):
    id = fields.Integer()
    hasBeenEdited = fields.Boolean()
    sources = fields.List(fields.Dict())
    receivers = fields.List(fields.Dict())
    taskType = fields.Enum(TaskType, required=True)
    settingsPreset = fields.Enum(Setting, required=True)
    status = fields.Enum(Status, required=True)
    simulationRunId = fields.Integer(allow_none=True)
    meshId = fields.Integer(allow_none=True)
    createdAt = fields.String()
    updatedAt = fields.String()
    completedAt = fields.String(allow_none=True)


class SimulationUpdateBodySchema(SimulationSchema):
    class Meta:
        id = EXCLUDE  # To ignore the field
        status = EXCLUDE
        simulationRunId = EXCLUDE
        createdAt = EXCLUDE
        updatedAt = EXCLUDE
        completedAt = EXCLUDE
        modelId = EXCLUDE


class SimulationByModelQuerySchema(Schema):
    modelId = fields.Integer(required=True)


class SimulationRunCreateSchema(Schema):
    simulationId = fields.Integer()


class SimulationWithModelInfoSchema(SimulationSchema):
    model = fields.Nested(ModelInfoBasicSchema)


class SimulationRunSchema(Schema):
    id = fields.Integer()
    sources = fields.List(fields.Dict())
    receivers = fields.List(fields.Dict())
    taskType = fields.Enum(TaskType, required=True)
    settingsPreset = fields.Enum(Setting, required=True)
    status = fields.Enum(Status, required=True)
    layerIdByMaterialId = fields.Dict()
    solverSettings = fields.Dict()
    createdAt = fields.String()
    updatedAt = fields.String()
    completedAt = fields.String()
    simulation = fields.Nested(SimulationWithModelInfoSchema)
