# app.py

import sqlite3
import bcrypt
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for

# --- 1. CONFIGURACIÓN DE FLASK ---
app = Flask(__name__, template_folder='.')

# --- 2. CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_FILE = "database.db"

def initialize_database():
    """Crea la base de datos y las tablas si no existen."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('alumno', 'profesor', 'admin'))
    );
    ''')
    # Aquí puedes añadir la creación de otras tablas como 'quizzes' en el futuro
    conn.commit()
    conn.close()
    print("Base de datos verificada/inicializada correctamente.")

# --- 3. FUNCIONES DE UTILIDAD PARA LA BASE DE DATOS ---
def get_db_connection():
    """Crea una conexión a la base de datos."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hashea la contraseña de forma segura."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed):
    """Verifica si una contraseña coincide con su hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- 4. RUTAS PARA SERVIR PÁGINAS HTML ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/registration_success')
def registration_success_page():
    name = request.args.get('name')
    email = request.args.get('email')
    role = request.args.get('role')
    return render_template('registration_success.html', name=name, email=email, role=role)

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

# --- 5. API DE LOGIN/SIGNUP ---
@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    username = data.get('email')
    password = data.get('password')
    role = data.get('role')
    if not (username and password and role):
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    if conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone():
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
    data = request.get_json()
    username = data.get('email')
    password = data.get('password')
    if not (username and password):
        return jsonify({'success': False, 'message': 'Correo y contraseña son obligatorios.'}), 400
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and check_password(password, user['password_hash']):
        user_data = {'username': user['username'], 'role': user['role']}
        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso.', 'user': user_data})
    else:
        return jsonify({'success': False, 'message': 'Correo o contraseña incorrectos.'}), 401

# --- 6. APIS PARA EL PANEL DE ADMINISTRADOR ---
@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    conn = get_db_connection()
    students_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'alumno'").fetchone()[0]
    teachers_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'profesor'").fetchone()[0]
    quizzes_count = 0  # Placeholder
    conn.close()
    stats = {'students': students_count, 'teachers': teachers_count, 'quizzes': quizzes_count}
    return jsonify(stats)

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM users ORDER BY role").fetchall()
    conn.close()
    user_list = [dict(user) for user in users]
    return jsonify(user_list)

@app.route('/api/admin/users/delete', methods=['POST'])
def delete_user():
    user_id = request.get_json().get('id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Falta el ID del usuario.'}), 400
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Usuario eliminado exitosamente.'})

@app.route('/api/admin/users/add', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not (username and password and role):
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'}), 400

    conn = get_db_connection()
    if conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Este correo electrónico ya está registrado.'}), 409

    password_hash = hash_password(password)
    conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                   (username, password_hash, role))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Usuario añadido exitosamente.'})

# --- 7. INICIO DE LA APLICACIÓN ---
initialize_database()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860, debug=True)
