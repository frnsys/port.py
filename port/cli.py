import os
import json
import click
import shutil
from click import echo
from port.server import create_app
from port.compile import compile_rss, compile_file

base = os.path.expanduser('~/.port')


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
    # Load site-specific config
    path = os.path.join(base, site_name + '.json')
    conf = json.load(open(path, 'r'))

    # Prep paths
    site_dir = conf['SITE_DIR']
    conf['BUILD_DIR'] = os.path.join(site_dir, '.build')
    conf['ASSET_DIR'] = os.path.join(site_dir, 'assets')
    theme = os.path.join(base, 'themes', conf['THEME'])

    # gogogo
    app = create_app(static_folder=theme, template_folder=theme, **conf)
    app.run(host='0.0.0.0', debug=True, port=port)


@cli.command()
@click.argument('site_name')
def create(site_name):
    """
    Create a new site
    """
    theme_dir = os.path.join(base, 'themes')
    if not os.path.exists(base):
        os.makedirs(base)

        default_themes = os.path.join(os.path.dirname(__file__), '../themes')
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
def compile(site_name):
    """
    Compile a site
    """
    # TO DO cleanup

    # Load site-specific config
    path = os.path.join(base, site_name + '.json')
    conf = json.load(open(path, 'r'))
    site_dir = conf['SITE_DIR']

    # Get all files and compile
    posts_by_category = {}
    categories = [c for c in os.listdir(site_dir)
                    if os.path.isdir(os.path.join(site_dir, c))
                    and c != 'assets'
                    and not c.startswith('.')]
    for cat in categories:
        path = os.path.join(site_dir, cat)
        posts_by_category[cat] = [compile_file(os.path.join(path, f)) for f in os.listdir(path) if f.endswith('.md')]
    posts = sum(posts_by_category.values(), [])

    # Remove existing build
    build_dir = os.path.join(site_dir, '.build')
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    # Write files
    for post, build_slug in posts:
        post_path = os.path.join(build_dir, build_slug + '.json')
        json.dump(post, open(post_path, 'w'))

    # Write RSS files
    rss_dir = os.path.join(build_dir, 'rss')
    os.makedirs(rss_dir)
    for cat in categories:
        rss_path = os.path.join(rss_dir, '{}.xml'.format(cat))
        new_posts = [p for p, bs in posts_by_category[cat] if not p['draft']][:20]
        compile_rss(new_posts, conf, rss_path)

    new_posts = [p for p, bs in posts if not p['draft']][:20]
    rss_path = os.path.join(rss_dir, 'rss.xml')
    compile_rss(new_posts, conf, rss_path)

    echo('Compiled!')
