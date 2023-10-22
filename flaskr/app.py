from flask import Flask, request, render_template, redirect, url_for, session
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
from flask import jsonify

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

    def __init__(self, user_id, original_filename, conversion_format):
        self.user_id = user_id
        self.original_filename = original_filename
        self.conversion_format = conversion_format

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

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'username' in session:
        username = session['username']
        user_task_list = user_tasks.get(username, [])

        if request.method == 'POST':
            new_task = request.form.get('new_task')
            if new_task:
                user_task_list.append(new_task)
                user_tasks[username] = user_task_list

            # Verificar si se envió un archivo en la solicitud
            if 'file' in request.files:
                file = request.files['file']

                # Verificar si el archivo tiene un nombre válido
                if file.filename != '':
                    # Obtener el formato de destino seleccionado por el usuario
                    conversion_format = request.form.get('conversion_format')

                    if not conversion_format:
                        return jsonify({'error': 'Extensión de destino no especificada'}), 400

                    if not allowed_format(conversion_format):
                        return jsonify({'error': 'Extensión de destino no permitida'}), 400

                    try:
                        username = get_jwt()['identity']
                        user = User.query.filter_by(username=username).first()
                        user_id = user.id if user else None
                    except Exception as e:
                        print(f"Error al obtener usuario del token JWT: {str(e)}")
                        username = 'default_user'
                        user_id = None

                    # Crear el directorio de carga si no existe
                    upload_folder = app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)

                    # Crear una tarea de conversión en la base de datos
                    conversion_task = FileConversionTask(
                        user_id=user_id,
                        original_filename=file.filename,
                        conversion_format=conversion_format
                    )
                    db.session.add(conversion_task)
                    db.session.commit()

                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_folder, filename)

                    # Guardar el archivo cargado en el sistema de archivos
                    file.save(file_path)

                    input_path = file_path
                    output_path = os.path.join(upload_folder, f'converted_{filename}.{conversion_format}')

                    # Detectar el códec según el formato de destino
                    if conversion_format == 'mp4':
                        codec = 'libx264'
                    elif conversion_format == 'webm':
                        codec = 'libvpx'
                    else:
                        # Agrega lógica para otros formatos si es necesario
                        codec = 'libx264'

                    video = VideoFileClip(input_path)
                    video.write_videofile(output_path, codec=codec)

                    # Actualizar el estado de la tarea a "processed"
                    conversion_task.status = 'processed'
                    conversion_task.converted_filename = f'converted_{filename}.{conversion_format}'
                    db.session.commit()

                    # Agregar el ID de la tarea a la lista de tareas del usuario
                    user_task_list.append(f'Task ID {conversion_task.id}: Convert {filename} to {conversion_format}')
                    user_tasks[username] = user_task_list

                    # Flash para mostrar un mensaje de éxito
                    flash('Conversión exitosa', 'success')

                    return redirect(url_for('tasks'))

        return render_template('tasks.html', username=username, tasks=user_task_list)
    return 'You are not logged in. <a href="/api/auth/login">Login</a> or <a href="/api/auth/register">Register</a>'

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

@jwt_required()
@app.route('/api/convert', methods=['POST'])
def convert_file():
    # Verificar si se envió un archivo en la solicitud
    if 'file' not in request.files:
        return jsonify({'error': 'No se ha proporcionado ningún archivo'}), 400

    file = request.files['file']

    # Verificar si el archivo tiene un nombre válido
    if file.filename == '':
        return jsonify({'error': 'El archivo no tiene nombre'}), 400

    # Obtener la extensión de destino del archivo del formulario
    conversion_format = request.form.get('conversion_format')

    if not conversion_format:
        return jsonify({'error': 'Extensión de destino no especificada'}), 400

    if not allowed_format(conversion_format):
        return jsonify({'error': 'Extensión de destino no permitida'}), 400

    try:
        username = get_jwt()['identity']
        user = User.query.filter_by(username=username).first()
        user_id = user.id if user else None
    except Exception as e:
        print(f"Error al obtener usuario del token JWT: {str(e)}")
        username = 'default_user'
        user_id = None

    # Crear el directorio de carga si no existe
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    # Crear una tarea de conversión en la base de datos
    conversion_task = FileConversionTask(user_id=user_id, original_filename=file.filename, conversion_format=conversion_format)
    db.session.add(conversion_task)
    db.session.commit()

    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)

    # Guardar el archivo cargado en el sistema de archivos
    file.save(file_path)

    input_path = file_path
    output_path = os.path.join(upload_folder, f'converted_{filename}.{conversion_format}')

    video = VideoFileClip(input_path)
    video.write_videofile(output_path, codec='libx264')

    # Actualizar el estado de la tarea a "processed"
    conversion_task.status = 'processed'
    conversion_task.converted_filename = f'converted_{filename}.{conversion_format}'
    db.session.commit()

    return jsonify({'message': 'Conversión exitosa', 'task_id': conversion_task.id}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')

