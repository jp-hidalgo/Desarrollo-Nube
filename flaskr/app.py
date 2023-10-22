from flask import Flask, request, render_template, redirect, url_for, session
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key  = 'your_secret_key'

jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class FileConversionTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('file_conversion_tasks', lazy=True))
    original_filename = db.Column(db.String(255), nullable=False)
    converted_filename = db.Column(db.String(255))
    conversion_format = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='uploaded')

    def __init__(self, user, original_filename, conversion_format):
        self.user = user
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
        return f'Hello, {session["username"]}! <br/> You token is {session["token"]} <br/> <a href="/logout">Logout</a>'
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
@jwt_required()
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/tasks', methods=['GET', 'POST'])
@jwt_required()
def tasks():
    if 'username' in session:
        username = session['username']
        user_task_list = user_tasks.get(username, [])

        if request.method == 'POST':
            new_task = request.form.get('new_task')
            if new_task:
                user_task_list.append(new_task)
                user_tasks[username] = user_task_list

        return render_template('tasks.html', username=username, tasks=user_task_list)
    return 'You are not logged in. <a href="/api/auth/login">Login</a> or <a href="/api/auth/register">Register</a>'

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0')

    creo que lo que no esta funionando es la creacion con este bloque: if __name__ == '__main__':
        db.create_all()
        app.run(host='0.0.0.0') la linea que creo que no funciona es esta: db.create_all()