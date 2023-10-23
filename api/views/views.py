from api import app
from flask import request, render_template, redirect 
from flask import url_for, session, send_from_directory
from flask_jwt_extended import create_access_token

from api.models.models import User
from app import db


@app.route('/create_user')
def create_user():
    user = User(username='example_user', password='example_password')
    db.session.add(user)
    db.session.commit()
    return 'User created!'

@app.route('/')
def home():
    if 'username' in session:
        return f'Hello, {session["username"]}! <br/> You token is {session["token"]} <br/>  <a href="/tasks">Tasks</a> <br/>  <a href="/logout">Logout</a>'
    return 'You are not logged in. <a href="/api/auth/login">Login</a>'

@app.route('/api/auth/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return 'Username already exists. Please choose a different username.'
        users[username] = password
        return 'Registration successful. <a href="/api/auth/login">Login</a>'
    return render_template('register.html')

@app.route('/api/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            token_de_acceso = create_access_token(
                identity = username,
                expires_delta=False,
                 additional_claims={"username": username},
            )
            session['token'] = token_de_acceso

            return redirect(url_for('home'))
        return 'Invalid username or password'
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return 'Archivo no encontrado', 404

@app.route('/upload/<filename>')
def upload_file(filename):
    try:
        pass
    except:
        pass
    else:
        pass


UPLOAD_FOLDER = 'uploads'
ALLOWED_FORMATS = {'mp4', 'webm', 'avi', 'mpeg', 'wmv'}

def allowed_format(extension):
    return extension.lower() in ALLOWED_FORMATS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS