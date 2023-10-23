
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

                    input_path = file_path
                    output_path = os.path.join(upload_folder, f'converted_{filename}.{conversion_format}')

                    video = VideoFileClip(input_path)
                    video.write_videofile(output_path, codec='libx264')

                    converted_file_url = url_for('download_file', filename=f'converted_{filename}.{conversion_format}')
                    flash('Conversión exitosa', 'success')

                    # Agregar el ID de la tarea a la lista de tareas del usuario
                    user_task_list.append(f'Task: Convert {filename} to {conversion_format}')
                    user_tasks[username] = user_task_list

        return render_template('tasks.html', username=username, tasks=user_task_list, converted_file_url=converted_file_url)
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS