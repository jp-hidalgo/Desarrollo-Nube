from api.views.tasks import UPLOAD_FOLDER

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key  = 'your_secret_key'

jwt = JWTManager(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/cars_api"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://flask_celery:flask_celery@db:5432/flask_clery"

db = SQLAlchemy(app)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')

