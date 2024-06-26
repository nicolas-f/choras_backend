from marshmallow import Schema, fields, post_load
from app.types import TaskType, Status, Setting

class SimulationSchema(Schema):
    id = fields.Integer()
    name = fields.String(required=True)
    description = fields.String(required=False)
    hasBeenEdited = fields.Boolean()

    sources = fields.List(fields.Dict())
    receivers = fields.List(fields.Dict())
    taskType = fields.Enum(TaskType, required=True)
    modelSettings = fields.Dict()
    settingsPreset = fields.Enum(Setting, required=True)
    solverSettings = fields.Dict()
    status = fields.Enum(Status, required=True)

    modelId = fields.Integer()
    simulationRunId = fields.Integer()

    meshId = fields.Integer()

    createdAt = fields.String()
    updatedAt = fields.String()
    completedAt = fields.String()


class ModelSettingsSchema(Schema):
    materialIdByObjectId = fields.Dict()
    scatteringByObjectId = fields.Dict()


class SolverSettingsSchema(Schema):
    dgSettings = fields.Dict()
    gaSettings = fields.Dict()


class SimulationCreateBodySchema(Schema):
    modelId = fields.Integer(required=True)
    name = fields.String(required=True)

    description = fields.String(required=False)
    simulationRun = fields.Integer(required=False)

    modelSettings = fields.Nested(ModelSettingsSchema)
    solverSettings = fields.Nested(SolverSettingsSchema)


class SimulationRunSchema(Schema):
    id = fields.Integer()
    name = fields.String(required=True)
    description = fields.String(required=False)
    hasBeenEdited = fields.Boolean()

    sources = fields.List(fields.Dict())
    receivers = fields.List(fields.Dict())
    taskType = fields.String()
    modelSettings = fields.Dict()
    settingsPreset = fields.String()
    solverSettings = fields.Dict()
    status = fields.String()

    modelId = fields.Integer()
    simulationRunId = fields.Integer()

    meshId = fields.Integer()

    createdAt = fields.String()
    updatedAt = fields.String()
    completedAt = fields.String()


class SimulationByModelQuerySchema(Schema):
    modelId = fields.Integer(required=True)
