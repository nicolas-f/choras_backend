from datetime import datetime

from app.db import db

class Export(db.Model):
    __tablename__ = "exports"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    zipFileName = db.Column(db.String(), nullable=False)
    preCsvFileName = db.Column(db.String(), nullable=False)
    
    simulationId = db.Column(db.Integer, db.ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    simulation = db.relationship("Simulation", backref=db.backref("export", uselist=False, cascade="all, delete"), foreign_keys=[simulationId])
    
    createdAt = db.Column(db.String(), default=datetime.now())
    updatedAt = db.Column(db.String(), default=datetime.now())