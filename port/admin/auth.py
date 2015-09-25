from functools import wraps
from flask import Response, request, current_app


def check_auth(username, password):
    conf = current_app.config
    return username == conf['ADMIN_USER'] and password == conf['ADMIN_PASS']


def authenticate():
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
