# app.py

import sqlite3
import bcrypt
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for

# --- 1. CONFIGURACIÓN DE FLASK ---
# Se le indica a Flask que los archivos HTML (templates) están en el mismo directorio
app = Flask(__name__, template_folder='.')

# --- 2. CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_FILE = "database.db"

def initialize_database():
    """
    Crea la base de datos y todas las tablas si no existen.
    Esto hace que la aplicación sea autocontenida y no necesite ejecutar setup_database.py.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Tabla de Usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE, -- Usaremos el email como username
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('alumno', 'profesor', 'admin'))
    );
    ''')

    # Tabla de Documentos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        uploaded_by_id INTEGER,
        FOREIGN KEY (uploaded_by_id) REFERENCES users(id)
    );
    ''')

    # Tabla de Quizzes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        document_id INTEGER,
        created_by_id INTEGER,
        FOREIGN KEY (document_id) REFERENCES documents(id),
        FOREIGN KEY (created_by_id) REFERENCES users(id)
    );
    ''')
    
    # ... (Puedes añadir aquí las demás tablas como 'questions' y 'results')

    conn.commit()
    conn.close()
    print("Base de datos verificada/inicializada correctamente.")

# --- 3. FUNCIONES DE UTILIDAD PARA LA BASE DE DATOS ---

def get_db_connection():
    """Crea una conexión a la base de datos."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por su nombre
    return conn

def hash_password(password):
    """Hashea la contraseña de forma segura usando bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed):
    """Verifica si una contraseña coincide con su hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- 4. RUTAS PARA SERVIR TUS PÁGINAS HTML (EL FRONTEND) ---

@app.route('/')
def index():
    # Tu página principal es login.html
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/registration_success')
def registration_success_page():
    # Toma los datos de la URL y los pasa al HTML para que se muestren
    name = request.args.get('name')
    email = request.args.get('email')
    role = request.args.get('role')
    return render_template('registration_success.html', name=name, email=email, role=role)

@app.route('/dashboard')
def dashboard_page():
    # En un futuro, aquí se podría verificar si el usuario ha iniciado sesión
    return render_template('dashboard.html')

# --- 5. API: EL "PUENTE" ENTRE TU JAVASCRIPT Y PYTHON ---

@app.route('/api/signup', methods=['POST'])
def api_signup():
    """Endpoint para registrar nuevos usuarios."""
    data = request.get_json()
    username = data.get('email') # Usamos el email como el nombre de usuario único
    password = data.get('password')
    role = data.get('role')

    if not (username and password and role):
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Este correo electrónico ya está registrado.'}), 409

    password_hash = hash_password(password)
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                   (username, password_hash, role))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '¡Registro exitoso!'})

@app.route('/api/login', methods=['POST'])
def api_login():
    """Endpoint para iniciar sesión."""
    data = request.get_json()
    username = data.get('email')
    password = data.get('password')

    if not (username and password):
        return jsonify({'success': False, 'message': 'Correo y contraseña son obligatorios.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password(password, user['password_hash']):
        # Si el login es correcto, enviamos los datos del usuario al frontend
        user_data = {
            'username': user['username'],
            'role': user['role']
        }
        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso.', 'user': user_data})
    else:
        # Si no, enviamos un error de autenticación
        return jsonify({'success': False, 'message': 'Correo o contraseña incorrectos.'}), 401

# --- 6. (FUTURO) API PARA EL TUTOR DE IA ---
# @app.route('/api/ask_tutor', methods=['POST'])
# def ask_tutor():
#     # Aquí integraremos la lógica de LangChain
#     question = request.get_json().get('question')
#     # ...procesar con LangChain...
#     # answer = qa_chain.run(question)
#     answer = f"Respuesta de la IA para: {question}"
#     return jsonify({'answer': answer})


# --- 7. INICIO DE LA APLICACIÓN ---

# Llamamos a esta función al inicio para asegurar que la BD y las tablas existan
initialize_database()

if __name__ == "__main__":
    # Esta sección se usa solo cuando ejecutas 'python app.py' en tu computadora.
    # Gunicorn (en Hugging Face) no la usará, pero es vital para probar localmente.
    app.run(host='0.0.0.0', port=7860, debug=True)
