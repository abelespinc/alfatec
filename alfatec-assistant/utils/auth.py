from quart import session, redirect, url_for
from functools import wraps
from utils.models import User
from utils.users import load_users

def authenticate(username, password):
    """Valida si el usuario existe y la contraseña es correcta usando el JSON."""
    users = load_users()
    user = users.get(username)
    if user and user['password'] == password:
        return User(username, user['name'], user.get('role', 'Usuario Básico'))
    return None

def login_user(user):
    session['user'] = {'username': user.username, 'name': user.name, 'role': user.role}

def logout_user():
    session.pop('user', None)

def login_required(func):
    """Middleware para proteger rutas que requieren autenticación."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return await func(*args, **kwargs)
    return wrapper
