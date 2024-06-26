from marshmallow import Schema, fields, post_load
from app.services import file_service


class SimulationSchema(Schema):
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

    createdAt = fields.DateTime(format="%Y-%m-%d %H:%M:%S")
    updatedAt = fields.DateTime(format="%Y-%m-%d %H:%M:%S")
    completedAt = fields.DateTime(format="%Y-%m-%d %H:%M:%S")


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

    createdAt = fields.DateTime(format="%Y-%m-%d %H:%M:%S")
    updatedAt = fields.DateTime(format="%Y-%m-%d %H:%M:%S")
    completedAt = fields.DateTime(format="%Y-%m-%d %H:%M:%S")


class SimulationByModelQuerySchema(Schema):
    modelId = fields.Integer(required=True)
