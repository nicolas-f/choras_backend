from datetime import datetime

from app.db import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    group = db.Column(db.String, nullable=False)
    models = db.relationship("Model", backref="project", cascade="all, delete")

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
