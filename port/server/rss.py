from flask import Blueprint, current_app, send_from_directory

bp = Blueprint('rss', __name__, url_prefix='/rss')


@bp.route('/')
def index():
    """
    RSS feed for everything
    """
    return send_from_directory(current_app.fm.rss_dir, 'rss.xml')


@bp.route('/<category>')
def category(category):
    """
    RSS feed for a category
    """
    return send_from_directory(current_app.fm.rss_dir, '{}.xml'.format(category))
