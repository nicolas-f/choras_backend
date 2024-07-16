from marshmallow import Schema, fields, post_load, EXCLUDE
from app.types import TaskType, Status, Setting


class SolverSettingsSchema(Schema):
    dgSettings = fields.Dict()
    gaSettings = fields.Dict()


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