from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class FileConversionTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('file_conversion_tasks', lazy=True))
    original_filename = db.Column(db.String(255), nullable=False)
    converted_filename = db.Column(db.String(255))
    conversion_format = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='uploaded')

    def __init__(self, user_id, original_filename, conversion_format):
        self.user_id = user_id
        self.original_filename = original_filename
        self.conversion_format = conversion_format