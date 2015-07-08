import math
from flask import Blueprint, request, render_template, current_app, abort, send_from_directory
from port.models import Post, Meta, Category

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """
    Index for all categories
    """
    conf = current_app.config
    per_page = int(conf.get('PER_PAGE'))

    posts = Post.all()
    posts, page, last_page = _pagination(posts, per_page)

    return render_template('index.html', posts=posts, page=page+1,
                           last_page=last_page,
                           site_data=Meta(request))


@bp.route('/<category>')
def category(category):
    """
    Index for a category
    """
    conf = current_app.config

    cat = Category(category)
    posts = Post.for_category(category)

    per_page = cat.per_page if hasattr(cat, 'per_page') else int(conf.get('PER_PAGE'))
    template = cat.template if hasattr(cat, 'template') else 'category.html'

    posts, page, last_page = _pagination(posts, per_page)
    return render_template(template, posts=posts, page=page+1,
                           category=cat,
                           last_page=last_page,
                           site_data=Meta(request))


@bp.route('/<category>/<slug>')
def post(category, slug):
    """
    Show a single post;
    The slug is the filename of the original markdown file
    """
    post = Post.single(category, slug)
    if post is not None:
        return render_template('single.html', post=post,
                                site_data=Meta(request))

    abort(404)


@bp.route('/assets/<path:filename>')
def assets(filename):
    """
    Handle assets for this site
    (the actual static path is used to serve theme files)
    """
    return send_from_directory(current_app.fm.asset_dir, filename)


def _pagination(posts, per_page):
    page = int(request.args.get('p', 1))
    page = max(page - 1, 0)

    if per_page == 0:
        if page > 0:
            abort(404)
        return posts, page, 0

    n = per_page * page
    m = per_page * (page + 1)

    N = len(posts)
    if n >= N:
        abort(404)

    last_page = math.ceil(N/per_page)
    return posts[n:m], page, last_page

