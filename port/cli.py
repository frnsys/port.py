import os
import yaml
import click
import shutil
import subprocess
from click import echo
from port.build import build_site

base = os.path.expanduser('~/.port')


def site_config(site_name):
    path = os.path.join(base, site_name + '.yaml')
    return yaml.load(open(path, 'r', encoding='utf8'))


@click.group()
def cli():
    pass


@cli.command()
@click.argument('site_name')
def create(site_name):
    """create a new site"""
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

    # create the site directories
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
    """build a site"""
    print('Building...')
    conf = site_config(site_name)
    build_site(conf, base)
    echo('Built!')


@cli.command()
@click.argument('site_name')
@click.argument('remote')
def sync(site_name, remote):
    """a convenience command to sync a site's files to a remote folder"""
    conf = site_config(site_name)

    # prep paths
    site_dir = conf['SITE_DIR']
    site_dir = os.path.expanduser(site_dir)

    subprocess.call([
        'rsync',
        '-ravu',
        site_dir + '/',
        remote,
        '--delete'
    ])
