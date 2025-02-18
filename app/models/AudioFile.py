from datetime import datetime
from config import DefaultConfig

from app.db import db


class AudioFile(db.Model):
    __tablename__ = "audio_files"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    path = db.Column(db.String(), nullable=False, default=DefaultConfig.AUDIO_FILE_FOLDER)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    isUserFile = db.Column(db.Boolean(), default=False)

    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
