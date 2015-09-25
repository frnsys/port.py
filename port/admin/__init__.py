import re
from functools import wraps
from flask import Blueprint, Response, request, current_app, render_template, abort, jsonify
from port.models import Post, Meta

bp = Blueprint('admin',
               __name__,
               url_prefix='/control',
               static_folder='static',
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
    [X] edit body
    [ ] edit title
        [ ] should create slug automatically
        [ ] should move file if necessary
    [ ] edit category
        [ ] should move file if necessary
    [ ] toggle draft
    [ ] set published datetime
[ ] new category
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


punct = r'[ !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+'
def slugify(text, delim=u'_'):
    """
    Simple slugifier
    """
    for p in punct:
        text = text.strip(p)
    return re.sub(punct, delim, text.lower())


@bp.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    if request.method == 'GET':
        posts = Post.all()
        return render_template('admin/index.html', posts=posts,
                            categories=Meta(request).categories)
    elif request.method == 'POST':
        data = request.get_json()
        slug = slugify(data['title'])
        cat = data['category']

        post = Post.single(cat, slug)
        if post is not None:
            abort(409) # conflict

        else:


@bp.route('/<category>/<slug>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@requires_auth
def post(category, slug):
    if request.method == 'GET':
        post = Post.single(category, slug)
        if post is None:
            abort(404)
        return render_template('admin/edit.html', post=post,
                               categories=Meta(request).categories)

    elif request.method == 'PUT':
        data = request.get_json()
        slug = slugify(data['title'])
        print(slug)
        print(data)
        return jsonify(success=True)

    elif request.method == 'DELETE':
        pass
