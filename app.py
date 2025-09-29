# app.py

import sqlite3
import bcrypt
import os
from flask import Flask, request, jsonify, render_template, redirect, url_for

# ... (El código de configuración y las funciones de utilidad no cambian) ...
app = Flask(__name__, template_folder='.')
DB_FILE = "database.db"
def initialize_database():
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
    conn.commit()
    conn.close()
    print("Base de datos verificada/inicializada correctamente.")
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
# ... (Las rutas para servir páginas HTML y las APIs de login/signup no cambian) ...
@app.route('/')
def index(): return render_template('login.html')
@app.route('/signup')
def signup_page(): return render_template('signup.html')
@app.route('/registration_success')
def registration_success_page():
    name = request.args.get('name')
    email = request.args.get('email')
    role = request.args.get('role')
    return render_template('registration_success.html', name=name, email=email, role=role)
@app.route('/dashboard')
def dashboard_page(): return render_template('dashboard.html')
@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    username, password, role = data.get('email'), data.get('password'), data.get('role')
    if not (username and password and role): return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'}), 400
    conn = get_db_connection()
    if conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Este correo electrónico ya está registrado.'}), 409
    password_hash = hash_password(password)
    conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '¡Registro exitoso!'})
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username, password = data.get('email'), data.get('password')
    if not (username and password): return jsonify({'success': False, 'message': 'Correo y contraseña son obligatorios.'}), 400
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and check_password(password, user['password_hash']):
        user_data = {'username': user['username'], 'role': user['role']}
        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso.', 'user': user_data})
    else: return jsonify({'success': False, 'message': 'Correo o contraseña incorrectos.'}), 401
# ... (Las APIs de stats, delete_user y add_user no cambian) ...
@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    conn = get_db_connection()
    stats = {
        'students': conn.execute("SELECT COUNT(*) FROM users WHERE role = 'alumno'").fetchone()[0],
        'teachers': conn.execute("SELECT COUNT(*) FROM users WHERE role = 'profesor'").fetchone()[0],
        'quizzes': 0
    }
    conn.close()
    return jsonify(stats)
@app.route('/api/admin/users/delete', methods=['POST'])
def delete_user():
    user_id = request.get_json().get('id')
    if not user_id: return jsonify({'success': False, 'message': 'Falta el ID del usuario.'}), 400
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Usuario eliminado exitosamente.'})
@app.route('/api/admin/users/add', methods=['POST'])
def add_user():
    data = request.get_json()
    username, password, role = data.get('email'), data.get('password'), data.get('role')
    if not (username and password and role): return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'}), 400
    conn = get_db_connection()
    if conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Este correo electrónico ya está registrado.'}), 409
    password_hash = hash_password(password)
    conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, password_hash, role))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Usuario añadido exitosamente.'})


# /// CAMBIO IMPORTANTE AQUÍ ///
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    # Obtenemos el término de búsqueda de los parámetros de la URL (ej: /api/admin/users?search=alan)
    search_term = request.args.get('search', '')
    
    conn = get_db_connection()
    
    # Modificamos la consulta SQL para incluir un filtro de búsqueda
    query = "SELECT id, username, role FROM users WHERE username LIKE ? ORDER BY role"
    # El comodín '%' busca cualquier coincidencia parcial
    params = (f'%{search_term}%',)
    
    users = conn.execute(query, params).fetchall()
    conn.close()
    
    user_list = [dict(user) for user in users]
    return jsonify(user_list)

# --- INICIO DE LA APLICACIÓN ---
initialize_database()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860, debug=True)
