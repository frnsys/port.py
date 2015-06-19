import os
from flask import Blueprint, current_app, send_from_directory

bp = Blueprint('rss', __name__, url_prefix='/rss')


@bp.route('/')
def index():
    """
    RSS feed for everything
    """
    conf = current_app.config
    build_dir = conf.get('BUILD_DIR')
    rss_path = os.path.join(build_dir, 'rss')
    return send_from_directory(rss_path, 'rss.xml')


@bp.route('/<category>')
def category(category):
    """
    RSS feed for a category
    """
    conf = current_app.config
    build_dir = conf.get('BUILD_DIR')
    rss_path = os.path.join(build_dir, 'rss')
    return send_from_directory(rss_path, '{}.xml'.format(category))
