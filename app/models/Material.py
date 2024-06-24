from datetime import datetime

from app.db import db


class Material(db.Model):
    __tablename__ = "materials"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    category = db.Column(db.String(80), nullable=False)
    materialJson = db.Column(db.String(), nullable=False)
    materialMetadataJson = db.Column(db.String(), nullable=False)
    defaultAbsorption = db.Column(db.Double(), nullable=False)
    defaultScattering = db.Column(db.Double(), nullable=False)
    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())
