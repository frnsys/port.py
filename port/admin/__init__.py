import os
import re
from functools import wraps
from datetime import datetime
from flask import Blueprint, Response, request, current_app, render_template, abort, jsonify, url_for
from port.models import Post, Page, Meta, Category
from port.compile import build_site

bp = Blueprint('admin',
               __name__,
               url_prefix='/control',
               static_folder='static',
               template_folder='templates')


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
        return render_template('admin/index.html', categories=Meta(request).categories)
    elif request.method == 'POST':
        data = request.get_json()
        cat = data['category']
        cat_slug = slugify(data['category'])
        cat_dir = os.path.join(current_app.fm.site_dir, cat_slug)
        os.makedirs(cat_dir)
        with open(os.path.join(cat_dir, 'meta.yaml'), 'w') as f:
            f.write(cat_template.format(cat).strip())
        build_site(current_app.config)
        return jsonify(success=True)


cat_template = '''
name: {}
'''

post_template = '''
---
published_at: {published}
draft: {draft}
---

# {title}

{body}
'''


def posts_for_category(category):
    """
    Custom method for getting compiled posts for a category
    so we can also get drafts
    """
    cat_dir = current_app.fm.category_dir(category)
    files =  [os.path.join(cat_dir, f) for f in os.listdir(cat_dir)
                                       if f.endswith('.json')
                                       and f != 'meta.json']
    posts = [Post.from_file(f) for f in files]
    return Post._sort(posts)

def pages():
    raw_slugs = [f.replace('.json', '') for f in os.listdir(current_app.fm.bpages_dir)
                                        if f.endswith('.json')]
    return [slug[2:] if slug[0] == 'D' else slug[1:] for slug in raw_slugs]

class Pages():
    def __init__(self):
        self.name = 'Pages'
        self.slug = 'pages'


@bp.route('/<category>', methods=['GET', 'PUT', 'POST'])
@requires_auth
def category(category):
    if request.method == 'GET':
        if category == 'pages':
            posts = [Page(slug) for slug in pages()]
            for p in posts:
                p.category = Pages()
            bigcat = Pages()
        else:
            posts = posts_for_category(category)
            bigcat = Category(category)
        return render_template('admin/category.html', posts=posts, category=bigcat)

    elif request.method == 'POST':
        data = request.get_json()
        title = data['title']
        if not title:
            abort(400)
        slug = slugify(title)
        post = Post.single(category, slug)
        if post is not None:
            abort(409) # conflict
        else:
            ppath = post_path(category, slug)
            with open(ppath, 'w') as f:
                f.write(post_template.format(
                    published=datetime.now().strftime("%m.%d.%Y %H:%M"),
                    draft='true',
                    title=title,
                    body=''
                ).strip())
            build_site(current_app.config)
            return jsonify(slug=slug)

    elif request.method == 'PUT':
        # rename category
        data = request.get_json()
        cat = data['category']
        cat_slug = slugify(data['category'])
        cat_dir = os.path.join(current_app.fm.site_dir, category)
        cat_dir_ = os.path.join(current_app.fm.site_dir, cat_slug)
        with open(os.path.join(cat_dir, 'meta.yaml'), 'w') as f:
            f.write(cat_template.format(cat).strip())
        os.rename(cat_dir, cat_dir_)
        build_site(current_app.config)
        return jsonify(slug=cat_slug)


def post_path(category, slug):
    return os.path.join(current_app.fm.site_dir,
                        category,
                        '{}.md'.format(slug))


@bp.route('/<category>/<slug>', methods=['GET', 'PUT', 'DELETE'])
@requires_auth
def post(category, slug):
    if category == 'pages':
        post = Page(slug)
        post.category = Pages()
    else:
        post = Post.single(category, slug)
    if post is None:
        abort(404)

    if request.method == 'GET':
        return render_template('admin/edit.html', post=post,
                               categories=Meta(request).categories + [Pages()])

    elif request.method == 'PUT':
        data = request.get_json()
        slug_ = slugify(data['title'])
        cat_ = data['category']

        ppath = post_path(category, slug)
        with open(ppath, 'w') as f:
            f.write(post_template.format(
                published=datetime.now().strftime('%m.%d.%Y %H:%M'),
                draft=data['draft'],
                title=data['title'],
                body=data['body']
            ).strip())

        ppath_ = post_path(cat_, slug_)

        moved = False
        if ppath != ppath_:
            moved = True
            os.rename(ppath, ppath_)

        build_site(current_app.config)

        if moved:
            return jsonify(success=True, url=url_for('admin.post', category=cat_, slug=slug_))
        else:
            return jsonify(success=True, url=False)

    elif request.method == 'DELETE':
        # just in case, don't actually delete the file...
        trash_dir = os.path.join(current_app.fm.site_dir, '.trash')
        if not os.path.exists(trash_dir):
            os.makedirs(trash_dir)
        ppath = post_path(category, slug)
        trashed_post_path = os.path.join(trash_dir, '{}__{}.md'.format(slug, datetime.now().strftime('%m_%d_%Y_%H_%M')))
        os.rename(ppath, trashed_post_path)
        build_site(current_app.config)
        return jsonify(success=True)
