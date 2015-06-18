from flask import Blueprint, current_app, render_template

bp = Blueprint('errors', __name__)


@bp.app_errorhandler(404)
def not_found(error):
    conf = current_app.config
    return render_template('404.html', site_data=conf), 404


@bp.app_errorhandler(500)
def internal_error(error):
    conf = current_app.config
    return render_template('500.html', site_data=conf), 500
