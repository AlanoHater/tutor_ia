# app.py

import gradio as gr
import sqlite3
import hashlib

# --- Lógica de Base de Datos y Autenticación ---

def hash_password(password):
    """Función de hash consistente con la de setup_database.py."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """Verifica el usuario contra la base de datos y devuelve su rol."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    
    cursor.execute(
        "SELECT role FROM users WHERE username = ? AND password_hash = ?",
        (username, hashed_password)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]  # Devuelve el rol (ej: 'alumno')
    else:
        return None

# --- Función de Login para Gradio ---

def login_flow(username, password):
    """Controla el flujo de la interfaz de Gradio al hacer login."""
    role = verify_user(username, password)
    
    if role:
        # Login exitoso: Oculta el login, muestra la app principal
        # y personaliza el mensaje de bienvenida.
        return (
            gr.update(visible=False), 
            gr.update(visible=True), 
            f"### Bienvenido, **{username}** (Rol: {role.capitalize()}) 🚀"
        )
    else:
        # Login fallido: Mantenemos todo como está. 
        # (En el futuro, podríamos añadir un mensaje de error)
        return gr.update(visible=True), gr.update(visible=False), ""

# --- Diseño de la Interfaz ---

gemini_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
body { font-family: 'Inter', sans-serif; background-color: #f0f4f9; }
.gradio-container { max-width: 900px !important; margin: auto !important; padding-top: 2rem; }
.primary { background-color: #1a73e8 !important; color: white !important; }
"""

with gr.Blocks(css=gemini_css, theme=gr.themes.Soft(primary_hue="blue")) as demo:
    
    # --- Grupo de Login (Visible al inicio) ---
    with gr.Group(visible=True) as login_group:
        with gr.Row():
            gr.Column(scale=1)
            with gr.Column(scale=2):
                gr.Markdown("<h1 style='text-align:center;'>Tutor IA</h1>")
                user_textbox = gr.Textbox(label="Usuario", placeholder="Escribe tu usuario...")
                pass_textbox = gr.Textbox(label="Contraseña", type="password", placeholder="Escribe tu contraseña...")
                login_button = gr.Button("Iniciar Sesión", variant="primary")
            gr.Column(scale=1)
            
    # --- Grupo Principal de la App (Oculto al inicio) ---
    with gr.Group(visible=False) as main_app_group:
        welcome_message = gr.Markdown("### Bienvenido")
        
        with gr.Tabs() as tabs:
            with gr.TabItem("🎓 Tutor IA"):
                gr.Markdown("Aquí irá la interfaz de chat principal.")
                # Futuro: gr.ChatInterface(...)
            with gr.TabItem("📊 Estadísticas"):
                gr.Markdown("Aquí irán las estadísticas del usuario.")

    # --- Evento de Click del Botón de Login ---
    login_button.click(
        fn=login_flow,
        inputs=[user_textbox, pass_textbox],
        outputs=[login_group, main_app_group, welcome_message]
    )

demo.launch()