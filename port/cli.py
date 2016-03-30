import os
import yaml
import click
import shutil
import subprocess
from click import echo
from port.server import create_app
from port.compile import build_site
from port.host import host_site, unhost_site
from port.fs import FileManager

base = os.path.expanduser('~/.port')


def site_config(site_name):
    path = os.path.join(base, site_name + '.yaml')
    return yaml.load(open(path, 'r', encoding='utf8'))

def app_for_site(site_name, port):
    """
    see host.py
    """
    conf = site_config(site_name)
    site_dir = conf['SITE_DIR']
    theme = os.path.join(base, 'themes', conf['THEME'])
    app = create_app(static_folder=theme, template_folder=theme, **conf)
    app.fm = FileManager(site_dir)

    if conf.get('DEBUG', False):
        app.config['DEBUG'] = True
        app.config['PROPAGATE_EXCEPTIONS'] = True

    return app


@click.group()
def cli():
    pass


@cli.command()
@click.argument('site_name')
@click.option('--port', default=5005)
def serve(site_name, port):
    """
    Serve a site
    """
    app = app_for_site(site_name, port)
    app.run(host='0.0.0.0', debug=True, port=port)


@cli.command()
@click.argument('site_name')
@click.argument('host_name')
@click.argument('user')
@click.option('--port', default=5005)
def host(site_name, host_name, user, port):
    """
    Host a site (experimental, only tested on Ubuntu 14.04)
    """
    host_site(site_name, host_name, user, port=port)


@cli.command()
@click.argument('site_name')
@click.argument('host_name')
def unhost(site_name, host_name):
    """
    Unhost a site
    """
    unhost_site(site_name, host_name)


@cli.command()
@click.argument('site_name')
def create(site_name):
    """
    Create a new site
    """
    theme_dir = os.path.join(base, 'themes')
    if not os.path.exists(base):
        os.makedirs(base)

        default_themes = os.path.join(os.path.dirname(__file__), 'themes')
        shutil.copytree(default_themes, theme_dir)

    path = os.path.join(base, site_name + '.yaml')
    if os.path.exists(path):
        echo('Site already exists! Remove the existing config at {} and retry.'.format(path))
        return


    themes = [t for t in os.listdir(theme_dir) if not t.startswith('.')]
    site_dir = input('Where will your site\'s files be located? ')
    site_name = input('What will you call your site? ')
    site_url = input('What url will your site be at? ')
    site_desc = input('How would you describe your site? ')
    per_page = input('How many posts should be shown per page? (use 0 to show all) ')
    theme = input('What theme will you use? Select from {} '.format(themes))

    if theme not in themes:
        theme = themes[0]

    site_dir = os.path.expanduser(site_dir)
    conf = {
        'SITE_DIR': site_dir,
        'SITE_NAME': site_name,
        'SITE_URL': site_url,
        'SITE_DESC': site_desc,
        'PER_PAGE': int(per_page),
        'THEME': theme
    }

    yaml.dump(conf, open(path, 'w'), default_flow_style=False)

    # Create the site directories
    if not os.path.exists(site_dir):
        os.makedirs(site_dir)

    for dir in ['assets', 'default_category', 'pages']:
        dir_path = os.path.join(site_dir, dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    echo('Site created.')
    echo('You can change your config by editing {}, make sure to restart the server afterwards.'.format(path))


@cli.command()
@click.argument('site_name')
def build(site_name):
    """
    Build a site
    """
    print('Building...')
    conf = site_config(site_name)
    build_site(conf)
    echo('Built!')


@cli.command()
@click.argument('site_name')
@click.argument('remote')
def sync(site_name, remote):
    """
    A convenience command to sync a site's files to a remote folder
    """
    conf = site_config(site_name)

    # Prep paths
    site_dir = conf['SITE_DIR']
    site_dir = os.path.expanduser(site_dir)

    subprocess.call([
        'rsync',
        '-ravu',
        site_dir + '/',
        remote,
        '--delete'
    ])
