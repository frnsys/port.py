import os
import json
import click
import shutil
import subprocess
from click import echo
from port.server import create_app
from port.compile import build_site
from port.host import host_site, unhost_site

base = os.path.expanduser('~/.port')


def app_for_site(site_name, port):
    # Load site-specific config
    path = os.path.join(base, site_name + '.json')
    conf = json.load(open(path, 'r'))

    # Prep paths
    site_dir = conf['SITE_DIR']
    conf['BUILD_DIR'] = os.path.join(site_dir, '.build')
    conf['ASSET_DIR'] = os.path.join(site_dir, 'assets')
    theme = os.path.join(base, 'themes', conf['THEME'])

    return create_app(static_folder=theme, template_folder=theme, **conf)


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

    path = os.path.join(base, site_name + '.json')
    if os.path.exists(path):
        echo('Site already exists! Remove the existing config at {} and retry.'.format(path))
        return


    themes = os.listdir(theme_dir)
    site_dir = input('Where will your site\'s files be located? ')
    site_name = input('What will you call your site? ')
    site_url = input('What url will your site be at? ')
    site_desc = input('How would you describe your site? ')
    per_page = input('How many posts should be shown per page? ')
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

    json.dump(conf, open(path, 'w'), indent=4, sort_keys=True)

    # Create the site directories
    if not os.path.exists(site_dir):
        os.makedirs(site_dir)

    for dir in ['assets', 'default_category']:
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
    # TO DO cleanup
    print('Building...')

    # Load site-specific config
    path = os.path.join(base, site_name + '.json')
    conf = json.load(open(path, 'r'))
    build_site(conf)

    echo('Built!')


@cli.command()
@click.argument('site_name')
@click.argument('remote')
def sync(site_name, remote):
    """
    A convenience command to sync a site's files to a remote folder
    """
    # Load site-specific config
    path = os.path.join(base, site_name + '.json')
    conf = json.load(open(path, 'r'))

    # Prep paths
    site_dir = conf['SITE_DIR']

    subprocess.call([
        'rsync',
        '-ravu',
        site_dir + '/',
        remote,
        '--delete'
    ])
