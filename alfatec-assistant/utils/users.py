# utils/users.py
import json
import os
 
# Definimos la ruta al archivo JSON (se crea en la misma carpeta que este módulo)
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')
 
def load_users():
    """Carga y retorna los usuarios desde el archivo JSON.
       Si el archivo no existe, lo crea con un usuario por defecto."""
    if not os.path.exists(USERS_FILE):
        # Usuario por defecto (agregamos rol por defecto, por ejemplo, "Usuario Básico")
        default_users = {
            "alfatec.business": {"name": "alfatec business", "password": "alfatec1", "role": "Administrador"},
            "alfatec.tech": {"name": "alfatec tech", "password": "alfatec2", "role": "Administrador"},
            "alberto.delariva": {"name": "alberto delariva", "password": "alfatec3", "role": "Administrador"},
        }
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f, indent=4)
        return default_users
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}
 
def save_users(users):
    """Guarda el diccionario de usuarios en el archivo JSON."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)
 
def add_user(username, name, password, role):
    """Agrega un usuario nuevo; retorna False si ya existe."""
    users = load_users()
    if username in users:
        return False
    users[username] = {"name": name, "password": password, "role": role}
    save_users(users)
    return True
 
def update_user(username, name, password, role):
    """Actualiza los datos de un usuario; si no se proporciona una nueva contraseña, se mantiene la actual.
       Retorna False si el usuario no existe."""
    users = load_users()
    if username not in users:
        return False
    # Si password está vacío, se conserva la contraseña existente.
    if not password:
        password = users[username].get("password", "")
    users[username] = {"name": name, "password": password, "role": role}
    save_users(users)
    return True
 
 
def delete_user(username):
    """Elimina un usuario; retorna False si no existe."""
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        return True
    return False