from datetime import datetime

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

class Model(db.Model):
    __tablename__ = "models"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)

    sourceFileId = db.Column(db.Integer, nullable=False)
    outputFileId = db.Column(db.Integer, nullable=False)

    projectId = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)

    meshId = db.Column(db.Integer, db.ForeignKey('meshes.id', ondelete='SET NULL'), nullable=True)
    mesh = db.relationship("Mesh", cascade="all, delete", foreign_keys=[meshId])

    simulations = db.relationship("Simulation", backref="model", cascade="all, delete")
    hasGeo = db.Column(db.Boolean, nullable=False, default=False)

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())


    @property
    def simulation_count(self):
        return len(self.simulations) # Assuming 'simulations' is the backref in Simulation model
