import os
import math
from flask import Blueprint, request, render_template, current_app, abort, send_from_directory
from port.models import Post, Meta

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """
    Index for all categories
    """
    conf = current_app.config
    build_dir = conf.get('BUILD_DIR')
    per_page = int(conf.get('PER_PAGE'))

    files = [f for f in os.listdir(build_dir)
             if f.endswith('.json')
             and not f.startswith('D')]
    files = sorted(files, key=lambda f: int(f.split('_')[0]), reverse=True)

    page = int(request.args.get('p', 1))
    page = max(page - 1, 0)

    n = per_page * page
    m = per_page * (page + 1)

    N = len(files)
    if n >= len(files):
        abort(404)

    posts = [Post(os.path.join(build_dir, f)) for f in files[n:m]]
    return render_template('index.html', posts=posts, page=page+1,
                           last_page=math.ceil(N/per_page),
                           site_data=Meta(conf, request))


@bp.route('/<category>')
def category(category):
    """
    Index for a category
    """
    conf = current_app.config
    build_dir = conf.get('BUILD_DIR')
    per_page = int(conf.get('PER_PAGE'))

    files = [f for f in os.listdir(build_dir)
             if f.endswith('.json')
             and '_{}_'.format(category) in f
             and not f.startswith('D')]
    files = sorted(files, key=lambda f: int(f.split('_')[0]), reverse=True)

    page = int(request.args.get('p', 1))
    page = max(page - 1, 0)

    n = per_page * page
    m = per_page * (page + 1)

    N = len(files)
    if n >= N:
        abort(404)

    posts = [Post(os.path.join(build_dir, f)) for f in files[n:m]]
    return render_template('category.html', posts=posts, page=page+1,
                           last_page=math.ceil(N/per_page),
                           site_data=Meta(conf, request))


@bp.route('/<category>/<slug>')
def post(category, slug):
    """
    Show a single post;
    The slug is the filename of the original markdown file
    """
    conf = current_app.config
    build_dir = current_app.config.get('BUILD_DIR')
    cslug = '{0}_{1}'.format(category, slug)

    # meh
    for f in os.listdir(build_dir):
        if cslug in f:
            path = os.path.join(build_dir, f)
            post = Post(path)
            return render_template('single.html', post=post,
                                   site_data=Meta(conf, request))

    abort(404)


@bp.route('/assets/<path:filename>')
def assets(filename):
    """
    Handle assets for this site
    (the actual static path is used to serve theme files)
    """
    asset_dir = current_app.config.get('ASSET_DIR')
    return send_from_directory(asset_dir, filename)
