import math
import whoosh
from whoosh.qparser import QueryParser
from flask import Blueprint, request, render_template, current_app, abort, send_from_directory
from port.models import Post, Page, Meta, Category

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

    return render_template('index.html',
                           posts=posts, page=page+1,
                           last_page=last_page,
                           site_data=Meta(request))


@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(current_app.fm.asset_dir, 'favicon.ico')


@bp.route('/search')
def search():
    """
    Search posts
    """
    conf = current_app.config
    per_page = int(conf.get('PER_PAGE'))
    query = request.args.get('query', '')

    posts = []
    ix = whoosh.index.open_dir(current_app.fm.index_dir)
    with ix.searcher() as searcher:
        q = QueryParser('content', ix.schema).parse(query)
        results = searcher.search(q, limit=None)
        results.fragmenter.charlimit = None
        results.fragmenter.surround = 100
        results.formatter = whoosh.highlight.HtmlFormatter(tagname='span', classname='search-match')
        for r in results:
            post = Post.single(r['category'], r['slug'])
            post.search_highlight = r.highlights('content', text=post.plain)

            # If the result is only in the title, the highlight will be empty
            if not post.search_highlight:
                post.search_highlight = post.plain[:200]

            posts.append(post)

    posts, page, last_page = _pagination(posts, per_page)

    return render_template('search.html',
                           posts=posts, page=page+1,
                           last_page=last_page,
                           site_data=Meta(request))


@bp.route('/<slug>')
def category_page(slug):
    """
    Index for a category or a single page
    """
    conf = current_app.config

    # If we don't recognize this as a category,
    # try a page
    if slug not in current_app.fm.categories():
        try:
            page = Page(slug)
        except FileNotFoundError:
            abort(404)
        template = page.template if hasattr(page, 'template') else 'page.html'
        return render_template(template,
                            page=page,
                            site_data=Meta(request))

    cat = Category(slug)
    posts = Post.for_category(slug)

    per_page = cat.per_page if hasattr(cat, 'per_page') else int(conf.get('PER_PAGE'))
    template = cat.template if hasattr(cat, 'template') else 'category.html'

    posts, page, last_page = _pagination(posts, per_page)
    return render_template(template,
                           posts=posts, page=page+1,
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
        return render_template('single.html',
                               post=post,
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

