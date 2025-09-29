# setup_database.py

import sqlite3
import bcrypt

def hash_password(password):
    """Hashea la contraseña usando bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print("Creando tablas...")

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('alumno', 'profesor', 'admin'))
);
''')

# --- Tabla de Documentos ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    uploaded_by_id INTEGER,
    FOREIGN KEY (uploaded_by_id) REFERENCES users(id)
);
''')

# --- Tabla de Quizzes ---
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

# --- Tabla de Preguntas ---
# Guardaremos las opciones como un texto JSON: '["Opción A", "Opción B", ...]'
cursor.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    options TEXT, -- JSON list of strings
    correct_answer TEXT NOT NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
);
''')

# --- Tabla de Resultados ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
);
''')

print("Tablas creadas exitosamente.")

cursor.execute("SELECT COUNT(*) FROM users")
if cursor.fetchone()[0] == 0:
    print("Insertando usuarios de ejemplo...")
    users_to_add = [
        ('alumno1@example.com', hash_password('pass123'), 'alumno'),
        ('profesor1@example.com', hash_password('pass123'), 'profesor'),
        ('admin1@example.com', hash_password('pass123'), 'admin')
    ]
    cursor.executemany("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", users_to_add)
    print("Usuarios de ejemplo insertados.")
else:
    print("La tabla de usuarios ya contiene datos.")

conn.commit()
conn.close()

print("Base de datos configurada exitosamente en 'database.db'.")
