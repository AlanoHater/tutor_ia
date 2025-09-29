# app.py (Versión 3.0 - Autosuficiente)

import gradio as gr
import sqlite3
import hashlib

# --- LÓGICA DE CONFIGURACIÓN DE LA BASE DE DATOS ---
# (Hemos movido el contenido de setup_database.py aquí)

def initialize_database():
    """Crea las tablas y los usuarios de ejemplo si la base de datos no existe."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    print("Verificando la configuración de la base de datos...")

    # Comprueba si la tabla de usuarios ya existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if cursor.fetchone() is not None:
        print("La base de datos ya está configurada.")
        conn.close()
        return

    print("Base de datos no encontrada. Creando tablas...")

    # --- Creación de todas las tablas ---
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('alumno', 'profesor', 'admin'))
    );''')
    # ... (y las otras tablas)
    cursor.execute('''CREATE TABLE documents (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, uploaded_by_id INTEGER, FOREIGN KEY (uploaded_by_id) REFERENCES users(id));''')
    cursor.execute('''CREATE TABLE quizzes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, document_id INTEGER, created_by_id INTEGER, FOREIGN KEY (document_id) REFERENCES documents(id), FOREIGN KEY (created_by_id) REFERENCES users(id));''')
    cursor.execute('''CREATE TABLE questions (id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_id INTEGER NOT NULL, question_text TEXT NOT NULL, options TEXT, correct_answer TEXT NOT NULL, FOREIGN KEY (quiz_id) REFERENCES quizzes(id));''')
    cursor.execute('''CREATE TABLE results (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, quiz_id INTEGER NOT NULL, score REAL NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (student_id) REFERENCES users(id), FOREIGN KEY (quiz_id) REFERENCES quizzes(id));''')
    
    print("Tablas creadas exitosamente.")

    # --- Insertar Usuarios de Ejemplo ---
    print("Insertando usuarios de ejemplo...")
    users_to_add = [
        ('alumno1', hash_password('pass123'), 'alumno'),
        ('profesor1', hash_password('pass123'), 'profesor'),
        ('admin1', hash_password('pass123'), 'admin')
    ]
    cursor.executemany("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", users_to_add)
    print("Usuarios de ejemplo insertados.")

    conn.commit()
    conn.close()
    print("Base de datos configurada exitosamente.")

# --- Lógica de Autenticación (sin cambios) ---

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute(
        "SELECT role FROM users WHERE username = ? AND password_hash = ?",
        (username, hashed_password)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def login_flow(username, password):
    role = verify_user(username, password)
    if role:
        return (
            gr.update(visible=False), 
            gr.update(visible=True), 
            f"### Bienvenido, **{username}** (Rol: {role.capitalize()}) 🚀"
        )
    else:
        # Ahora devolvemos un error visible para el usuario
        return gr.update(visible=True), gr.update(visible=False), ""


# --- Inicialización ---
# ¡IMPORTANTE! Ejecutamos la función de configuración de la BD aquí, 
# justo antes de construir la interfaz.
initialize_database()


# --- Diseño de la Interfaz (sin cambios) ---

gemini_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
body { font-family: 'Inter', sans-serif; background-color: #f0f4f9; }
.gradio-container { max-width: 900px !important; margin: auto !important; padding-top: 2rem; }
.primary { background-color: #1a73e8 !important; color: white !important; }
"""

with gr.Blocks(css=gemini_css, theme=gr.themes.Soft(primary_hue="blue")) as demo:
    
    with gr.Group(visible=True) as login_group:
        with gr.Row():
            gr.Column(scale=1)
            with gr.Column(scale=2):
                gr.Markdown("<h1 style='text-align:center;'>Tutor IA</h1>")
                user_textbox = gr.Textbox(label="Usuario", placeholder="Escribe tu usuario...")
                pass_textbox = gr.Textbox(label="Contraseña", type="password", placeholder="Escribe tu contraseña...")
                login_button = gr.Button("Iniciar Sesión", variant="primary")
            gr.Column(scale=1)
            
    with gr.Group(visible=False) as main_app_group:
        welcome_message = gr.Markdown("### Bienvenido")
        with gr.Tabs() as tabs:
            with gr.TabItem("🎓 Tutor IA"):
                gr.Markdown("Aquí irá la interfaz de chat principal.")
            with gr.TabItem("📊 Estadísticas"):
                gr.Markdown("Aquí irán las estadísticas del usuario.")

    login_button.click(
        fn=login_flow,
        inputs=[user_textbox, pass_textbox],
        outputs=[login_group, main_app_group, welcome_message]
    )

demo.launch()
