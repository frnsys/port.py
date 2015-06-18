from flask import Flask, Blueprint
import pkgutil
import importlib


def create_app(package_name=__name__, package_path=__path__, static_folder='static', template_folder='templates', **config_overrides):
    app = Flask(package_name,
                static_url_path='/static',
                static_folder=static_folder,
                template_folder=template_folder)

    # Apply overrides.
    app.config.update(config_overrides)

    # Register blueprints.
    _register_blueprints(app, package_name, package_path)

    return app


def _register_blueprints(app, package_name, package_path):
    """
    Register all Blueprint instances on the
    specified Flask application found
    in all modules for the specified package.
    """
    results = []
    for _, name, _ in pkgutil.iter_modules(package_path):
        m = importlib.import_module('%s.%s' % (package_name, name))
        for item in dir(m):
            item = getattr(m, item)
            if isinstance(item, Blueprint):
                app.register_blueprint(item)
            results.append(item)
    return results
