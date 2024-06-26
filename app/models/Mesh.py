from datetime import datetime
from enum import Enum

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

class Mesh(db.Model):
    __tablename__ = "meshes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    modelId = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    model = db.relationship("Model", back_populates="mesh", foreign_keys=[modelId])

    taskId = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    task = db.relationship("Task", cascade="all, delete", foreign_keys=[taskId])

    simulation = db.relationship("Simulation", back_populates="mesh")

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
    completedAt = db.Column(db.String(), nullable=True)
