from datetime import datetime

from app.types import Task, Setting, Status

from app.db import db
from sqlalchemy import JSON


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

class SimulationRun(db.Model):
    __tablename__ = "simulationRuns"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    modelId = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    model = db.relationship("Model", back_populates="simulationRuns", foreign_keys=[modelId])

    simulationId = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=True)
    simulation = db.relationship("Simulation", foreign_keys=[simulationId])

    sources = db.Column(JSON, default=[])
    percentage = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum(Status), default=Status.Created)

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
    completedAt = db.Column(db.String(), nullable=True)
