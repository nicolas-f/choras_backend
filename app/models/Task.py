from datetime import datetime

from app.db import db
from app.types import TaskType, Status


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    taskType = db.Column(db.Enum(TaskType), default=TaskType.DE)
    status = db.Column(db.Enum(Status), default=Status.Created)
    message = db.Column(db.String, nullable=True)

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
    completedAt = db.Column(db.String(), nullable=True)
