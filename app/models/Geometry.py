from datetime import datetime

from app.db import db


class Geometry(db.Model):
    __tablename__ = "geometries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    inputModelUploadId = db.Column(db.Integer, nullable=False)
    outputModelId = db.Column(db.Integer, nullable=True)

    taskId = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    task = db.relationship("Task", cascade="all, delete", foreign_keys=[taskId])

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
