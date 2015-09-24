from functools import wraps
from flask import Blueprint, Response, request, current_app, render_template
from port.models import Post

bp = Blueprint('admin',
               __name__,
               url_prefix='/control',
               template_folder='templates')

"""
TODO:

[X] http basic auth
[X] specify admin: true
[X] specify admin username
[X] specify admin password
[ ] new post endpoint
[ ] delete post endpoint
[ ] save post endpoint
[ ] post editor
[ ] message flashing
"""


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


@bp.route('/')
@requires_auth
def index():
    posts = Post.all()
    return render_template('index.html', posts=posts)


@bp.route('/<slug>', methods=['GET', 'POST', 'PUT'])
@requires_auth
def post():
    if request.method == 'POST':
    posts = Post.all()
    return render_template('edit.html', posts=posts)
