import uuid
from datetime import datetime

from app.db import db


class File(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fileName = db.Column(db.String(), nullable=True)
    slot = db.Column(db.String(), default=uuid.uuid4().hex)

    size = db.Column(db.Integer, default=0)
    consumed = db.Column(db.Boolean(), default=False)

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
