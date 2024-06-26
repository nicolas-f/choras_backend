from datetime import datetime
from sqlalchemy import JSON

from app.types import TaskType, Setting, Status

from app.db import db


class Simulation(db.Model):
    __tablename__ = "simulations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)

    hasBeenEdited = db.Column(db.Boolean, nullable=False, default=False)
    sources = db.Column(JSON, default=[])
    receivers = db.Column(JSON, default=[])
    taskType = db.Column(db.Enum(TaskType), default=TaskType.DE)
    modelSettings = db.Column(JSON, default={
        "materialIdByObjectId": {},
        "scatteringByObjectId": {}
    })
    settingsPreset = db.Column(db.Enum(Setting), default=Setting.Default)
    solverSettings = db.Column(JSON, nullable=False)
    status = db.Column(db.Enum(Status), default=Status.Created)

    modelId = db.Column(db.Integer, db.ForeignKey('models.id', ondelete='CASCADE'), nullable=False)

    simulationRunId = db.Column(db.Integer, db.ForeignKey('simulationRuns.id', ondelete='CASCADE'), nullable=True)
    # TODO: handle simulationRun backdref and cascade here

    meshId = db.Column(db.Integer, db.ForeignKey('meshes.id'), nullable=True)
    mesh = db.relationship("Mesh", back_populates="simulation", foreign_keys=[meshId])

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
    completedAt = db.Column(db.String(), nullable=True)
