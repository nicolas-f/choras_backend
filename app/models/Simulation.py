from datetime import datetime
from sqlalchemy import JSON

from app.types import TaskType, Setting, Status

from app.db import db


# name: Optional[str] = None,
# type_: Optional[_TypeEngineArgument[_T]] = None,
# autoincrement: _AutoIncrementType = "auto",
# default: Optional[Any] = None,
# doc: Optional[str] = None,
# key: Optional[str] = None,
# index: Optional[bool] = None,
# unique: Optional[bool] = None,
# info: Optional[_InfoType] = None,
# nullable: Optional[
#     Union[bool, Literal[SchemaConst.NULL_UNSPECIFIED]]
# ] = SchemaConst.NULL_UNSPECIFIED,
# onupdate: Optional[Any] = None,
# primary_key: bool = False,
# server_default: Optional[_ServerDefaultType] = None,
# server_onupdate: Optional[FetchedValue] = None,
# quote: Optional[bool] = None,
# system: bool = False,
# comment: Optional[str] = None,

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

    modelId = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    model = db.relationship("Model", back_populates="simulations", foreign_keys=[modelId])

    simulationRunId = db.Column(db.Integer, db.ForeignKey('simulationRuns.id'), nullable=True)
    simulationRun = db.relationship("SimulationRun", cascade="all, delete", foreign_keys=[simulationRunId])

    meshId = db.Column(db.Integer, db.ForeignKey('meshes.id'), nullable=True)
    mesh = db.relationship("Mesh", back_populates="simulation", foreign_keys=[meshId])

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
    completedAt = db.Column(db.String(), nullable=True)
