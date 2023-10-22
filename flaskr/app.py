from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

users = {
    'user1': 'password1',
    'user2': 'password2',
}

# Define a dictionary to store user tasks (for demonstration purposes)
user_tasks = {
    'user1': ['Task 1', 'Task 2'],
    'user2': ['Task 3', 'Task 4'],
}

@app.route('/')
def home():
    if 'username' in session:
        return f'Hello, {session["username"]}! <a href="/logout">Logout</a>'
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
            
        return render_template('tasks.html', username=username, tasks=user_task_list)
    return 'You are not logged in. <a href="/api/auth/login">Login</a> or <a href="/api/auth/register">Register</a>'

if __name__ == '__main__':
    app.run(host='0.0.0.0')