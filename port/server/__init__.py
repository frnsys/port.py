from flask import Flask
from . import errors, routes, rss


def create_app(package_name=__name__, package_path=__path__, static_folder='static', template_folder='templates', **config_overrides):
    app = Flask(package_name,
                static_url_path='/static',
                static_folder=static_folder,
                template_folder=template_folder)

    app.config.update(config_overrides)

    app.register_blueprint(errors.bp)
    app.register_blueprint(routes.bp)
    app.register_blueprint(rss.bp)

    return app
