import asyncio
import time
import os
import uuid
import requests
import logging
import re
import quart
from quart import Quart, render_template, request, session, redirect, url_for, jsonify, flash
from flask_session import Session
from utils.chat_utils import SemanticQueryEngine, MaxRetriesExceededError
from utils.states import states
from utils.chat_kernel import ChatKernel
from utils.auth import authenticate, login_user, logout_user, login_required
from utils.progress import send_progress_message, progress_messages

#from quart_session import Session

#app = Flask(__name__)
app = Quart(__name__, static_url_path='/chatbot/static')

# Configurar Quart-Session para almacenar las sesiones en archivos
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp/session_files'  # Directorio donde se guardarán las sesiones
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True  # Firmar las cookies para mayor seguridad

Session(app)

# [SESSION CONFIGURATION]
app.secret_key = 'your_secret_key'  # Necesario para manejar las sesiones


# [GLOBAL VARIABLES]
INTERACTION_LIMIT = 6
USER = 'TEST'
MAIL = 'test@mail.com'
custom_flows = {
    "conversational": True,
    "consult": True
}


#Logging config
log_file = "/var/logs/chatbot_logs.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/')
async def index():
    return redirect(url_for('login'))  # ✅ Redirección inmediata a /login

    
# Ruta para login con logs detallados
@app.route('/login', methods=['GET', 'POST'])
async def login():
    try:
        logging.info("[LOGIN] Solicitud recibida en /login")
        print("[LOGIN] Solicitud recibida en /login")

        if request.method == 'POST':
            logging.info("[LOGIN] Método POST detectado")
            print("[LOGIN] Método POST detectado")

            form = await request.form
            username = form.get('username')
            password = form.get('password')

            logging.info(f"[LOGIN] Datos recibidos - Username: {username}")
            print(f"[LOGIN] Datos recibidos - Username: {username}")

            if not username or not password:
                logging.error("[LOGIN] Error: Falta username o contraseña")
                print("[LOGIN] Error: Falta username o contraseña")
                await flash("Debes ingresar un username y contraseña.")
                return redirect(url_for('login'))

            user = authenticate(username, password)

            if user:
                logging.info("[LOGIN] Usuario autenticado correctamente")
                print("[LOGIN] Usuario autenticado correctamente")

                session.clear()
                login_user(user)

                logging.info("[LOGIN] Redirigiendo al chatbot")
                print("[LOGIN] Redirigiendo al chatbot")

                return redirect(url_for('chatbot'))
            else:
                logging.warning("[LOGIN] Autenticación fallida")
                print("[LOGIN] Autenticación fallida")

                await flash("Usuario o contraseña incorrectos.")
                return redirect(url_for('login'))

        return await render_template('login.html')

    except Exception as e:
        logging.error(f"[LOGIN] Error inesperado: {str(e)}")
        print(f"[LOGIN] Error inesperado: {str(e)}")
        return "Internal Server Error", 500


@app.route('/logout')
async def logout():
    try:
        logging.info("[LOGOUT] Cierre de sesión iniciado")
        print("[LOGOUT] Cierre de sesión iniciado")

        # Asegurarse de que 'session' contiene 'user' antes de eliminarlo
        if 'user' in session:
            logout_user()
            logging.info("[LOGOUT] Usuario desconectado correctamente")
            print("[LOGOUT] Usuario desconectado correctamente")
        else:
            logging.warning("[LOGOUT] No había sesión activa")
            print("[LOGOUT] No había sesión activa")

        # Redirigir de manera segura a la página de login
        return redirect(url_for('login'))

    except Exception as e:
        logging.error(f"[LOGOUT] Error inesperado: {str(e)}")
        print(f"[LOGOUT] Error inesperado: {str(e)}")
        return "Internal Server Error", 500



@app.route('/progress')
async def progress():
    async def event_stream():
        while True:
            if progress_messages:
                yield f"data: {progress_messages[0]}\n\n"  # No borrar inmediatamente
                await asyncio.sleep(3)  # Esperar para que el frontend lo reciba
                progress_messages.pop(0)  # Luego de 3 segundos, borrar el mensaje
            else:
                yield "data: \n\n"  # Mantener la conexión abierta
                await asyncio.sleep(1)  # Reducir la carga del servidor
    
    return quart.Response(event_stream(), content_type='text/event-stream')


def show_chat_history():
    return session.get('chat_history', [])

@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
async def chatbot(state='default_es'):
    print('-----------GPT: CHATGPT PRINCIPAL FUNCTION RESPONSE START-----------')
    print('[CHATBOT] State: ',session.get('current_state', 0))
    print(f"[CHATBOT] User Session: {session.get('user', 'No user defined')}")
    print('[CHATBOT] Assistant Interactions:', session.get('interaction_count_assistant', 0) + 1)
    logging.info(f"Un usuario ha iniciado una conversación. Estado: {state}")

    # [VARIABLES]
    bot_icon = states[state]['bot_icon']
    user_icon = states[state]['user_icon']

    #user_id = get_or_create_user_id()
    session['current_state'] = state

    # [REFRESH LOGIC - CLEAN VARIABLES ON EVERY PAGE LOAD (GET REQUEST)]
    if request.method == 'GET':
        # Limpiar las variables de sesión cada vez que se carga o recarga la página
        session['chat_history'] = []
        #session['user'] = []

    # [EXTRA: STILL HANDLE THE REFRESH PARAMETER IF NEEDED]
    refresh = request.args.get('refresh', 'false') == 'true'

    if refresh:
        session['chat_history'] = []

    if state not in states:
        return "Estado no encontrado", 404

    if 'chat_history' not in session:
        session['chat_history'] = []

    if 'user_input' not in session:
        session['user_input'] = ""
    
    if  'response_assistant' not in session:
        session['response_assistant'] = ""

    if len(session['chat_history']) == 0:
        pass

    # [CHATBOT LOGIC]
    if request.method == 'POST':

        #user_input = request.form.get('user_input')
        form = await request.form
        user_input = form.get('user_input')
        logging.info(f"Mensaje del usuario: {user_input}")

        selected_model = form.get('selected_model', 'gpt-4o')  # Modelo seleccionado, predeterminado: gpt-4o

        session['selected_model'] = selected_model

        # Configurar el modelo en SemanticQueryEngine
        chat_kernel = ChatKernel(
            chat_history=session.get('chat_history', []),
            flows=custom_flows
        )
        session['chat_history'] = chat_kernel.chat_history

        if user_input: 

            session['user_input'] = user_input
            session.modified = True


            #response_assistant = asyncio.run(assistant.chat(user_input))
            try: 
                #response_assistant = await assistant.chat(user_input)
                response_assistant = await chat_kernel.handle_user_input(user_input)
                print('[GPT] Response: ',response_assistant)
                logging.info(f"Respuesta del asistente: {response_assistant}")
                print('-----------GPT: CHATGPT PRINCIPAL FUNCTION RESPONSE END-----------')

            except MaxRetriesExceededError as e:
                # Si ocurre el error de máximo reintentos, devolver un error 500
                print(f"Error: {str(e)}")
                return jsonify({"error": "Could not process your request. Please try again later."}), 411

            # Save the chat history
            session['chat_history'].append({"user": user_input, "assistant": response_assistant})
            session['response_assistant'] = response_assistant
            session.modified = True
            return jsonify(assistant_response=response_assistant)

    return await render_template(states[state]['render_template'], 
                            bot_icon=bot_icon,
                            user_icon=user_icon,
                            chat_history=show_chat_history(),
                            state=state,
                            selected_model=session.get('selected_model', 'gpt-4o')  # Modelo por defecto
                            )

if __name__ == '__main__':
    app.debug=True
    app.run(host='0.0.0.0', port=8504, debug=True,use_reloader=True)
