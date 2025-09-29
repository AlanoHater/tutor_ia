# app.py

import sqlite3
import bcrypt
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for

# --- Configuración de Flask ---
app = Flask(__name__, template_folder='.') # Le decimos que los HTML están en la raíz

# --- Lógica de la Base de Datos ---
DB_FILE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- RUTAS PARA SERVIR TUS PÁGINAS HTML ---

@app.route('/')
def index():
    # Sirve tu página de login principal
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/registration_success')
def registration_success_page():
    # Pasamos los parámetros de la URL a la plantilla
    name = request.args.get('name')
    email = request.args.get('email')
    role = request.args.get('role')
    return render_template('registration_success.html', name=name, email=email, role=role)

@app.route('/dashboard')
def dashboard_page():
    # Aquí iría la lógica para proteger la ruta
    # Por ahora, la servimos directamente
    return render_template('dashboard.html')

# --- API: EL "PUENTE" ENTRE FRONTEND Y BACKEND ---

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    username = data.get('email') # Usamos el email como username
    password = data.get('password')
    role = data.get('role')

    if not (username and password and role):
        return jsonify({'success': False, 'message': 'Faltan datos.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'El usuario ya existe.'}), 409

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
        return jsonify({'success': False, 'message': 'Faltan datos.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password(password, user['password_hash']):
        user_data = {
            'username': user['username'],
            'role': user['role']
        }
        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso.', 'user': user_data})
    else:
        return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos.'}), 401

# --- Lógica del Tutor de IA (La integraremos aquí más tarde) ---
# @app.route('/api/ask_tutor', methods=['POST'])
# def ask_tutor():
#     # ...
#     return jsonify({'answer': '...'})

# --- Iniciar la aplicación ---
if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        print("Base de datos no encontrada. Ejecuta setup_database.py primero.")
    app.run(debug=True) # debug=True te ayuda a ver errores mientras desarrollas
