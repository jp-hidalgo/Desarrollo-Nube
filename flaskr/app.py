from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt
from flask_sqlalchemy import SQLAlchemy
import os
import stat
import logging
import shutil
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
from flask import jsonify
from flask import send_file

app = Flask(__name__)
app.secret_key  = 'your_secret_key'

jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/site.db'

db = SQLAlchemy(app)


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



users = {
    'user1': 'password1',
    'user2': 'password2',
}

# Define a dictionary to store user tasks (for demonstration purposes)
user_tasks = {
    'user1': ['Task 1', 'Task 2'],
    'user2': ['Task 3', 'Task 4'],
}

@app.route('/create_user')
def create_user():
    user = User(username='example_user', password='example_password')
    db.session.add(user)
    db.session.commit()
    return 'User created!'

@app.route('/')
def home():
    if 'username' in session:
        return f'Hello, {session["username"]}! -->  <br/> You token is {session["token"]} <br/>  <a href="/tasks">Tasks</a> <br/>  <a href="/logout">Logout</a>'
    return 'You are not logged in. <a href="/api/auth/login">Login</a>'

@app.route('/api/auth/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return 'Username already exists. Please choose a different username.'
        users[username] = password
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()


        return 'Registration successful. <a href="/api/auth/login">Login</a>'
    return render_template('register.html')

@app.route('/api/auth/login', methods=['GET', 'POST'])
def login():


    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:

            chef = User.query.filter(
                User.username == username,
                User.password == password,
            ).first()


            session['id_user'] = chef.id

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

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'username' in session:
        username = session['username']
        user_task_list = user_tasks.get(username, [])
        converted_file_url = None  # Asigna un valor predeterminado

        if request.method == 'POST':
            new_task = request.form.get('new_task')
            if new_task:
                user_task_list.append(new_task)
                user_tasks[username] = user_task_list

            if 'file' in request.files:
                file = request.files['file']

                if file.filename != '':
                    conversion_format = request.form.get('conversion_format')

                    if not conversion_format:
                        return jsonify({'error': 'Extensión de destino no especificada'}), 400

                    if not allowed_format(conversion_format):
                        return jsonify({'error': 'Extensión de destino no permitida'}), 400

                    upload_folder = app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)

                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    os.chmod(file_path, 0o644)  # Cambiar permisos del archivo original

                    input_path = file_path
                    # Cambio: nombra el archivo convertido usando el mismo nombre base pero con la nueva extensión
                    output_filename = f"converted_{filename.rsplit('.', 1)[0]}.{conversion_format}"
                    output_path = os.path.join(upload_folder, output_filename)

                    video = VideoFileClip(input_path)
                    video.write_videofile(output_path, codec='libx264')
                    os.chmod(output_path, 0o644)  # Cambiar permisos del archivo convertido

                    # Agregar el ID de la tarea a la lista de tareas del usuario
                    user_task_list.append(f'Task: Convert {filename} to {conversion_format}')
                    user_tasks[username] = user_task_list

                    """taskFile = FileConversionTask(
                        user_id=session['id_user'],
                        original_filename=filename,
                        converted_filename=f'Task: Convert {filename} to {conversion_format}',
                        conversion_format=conversion_format,
                        status="Conv exitosa")
                    db.session.add(taskFile)
                    db.session.commit()"""

                    # Cambio: crea la URL para el archivo convertido usando la función url_for
                    converted_file_url = url_for('download_file', filename=output_filename)
                    flash('Conversión exitosa', 'success')

        #return render_template('tasks.html', id_user=session["id_user"], username=username, tasks=user_task_list, converted_file_url=converted_file_url)
        return render_template('tasks.html', username=username, tasks=user_task_list, converted_file_url=converted_file_url)
    return 'You are not logged in. <a href="/api/auth/login">Login</a> or <a href="/api/auth/register">Register</a>'

@app.route('/download/<filename>')
def download_file(filename):
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)

        # Logeamos los permisos del archivo
        file_stat = os.stat(file_path)
        permissions = stat.filemode(file_stat.st_mode)
        app.logger.info(f'Permissions for {file_path}: {permissions}')

        app.logger.info(f'Contenido del directorio "uploads" antes de la descarga: {os.listdir(upload_folder)}')

        # Utilizando send_file con ruta absoluta
        absolute_path = os.path.abspath(file_path)
        return send_file(absolute_path, as_attachment=True)
    except FileNotFoundError:
        app.logger.info(f'Contenido del directorio "uploads" después de no encontrar el archivo: {os.listdir(upload_folder)}')
        return 'Archivo no encontrado', 404

@jwt_required()
@app.route('/tasks/<int:id_task>', methods=['GET','POST'])
def get_task_by_id(id_task):
    id_task=id_task-1
    print("** llegue -> ", request.method )
    if 'username' in session:
        username = session['username']
        user_task_list = user_tasks.get(username, [])

        if id_task < 0 or id_task >= len(user_task_list):
            return 'Tarea no encontrada', 404  # Retorna un código 404 si el ID no existe
        else:
            task = user_task_list[id_task]
            return f'Tarea ID {id_task}: {task} <br/> volver a <a href="/tasks">tasks</a> '

    return 'You are not logged in. <a href="/api/auth/login">Login</a> or <a href="/api/auth/register">Register</a>'


@jwt_required()
@app.route('/tasks/<int:id_task>', methods=['GET','DELETE'])
def delete_task_by_id(id_task):
    id_task=id_task-1
    print("** llegue -> ", request.method )

    return f'eliminado {id_task}'

UPLOAD_FOLDER = 'uploads'
ALLOWED_FORMATS = {'mp4', 'webm', 'avi', 'mpeg', 'wmv'}

def allowed_format(extension):
    return extension.lower() in ALLOWED_FORMATS

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.logger.setLevel(logging.INFO)
    app.run(host='0.0.0.0')

