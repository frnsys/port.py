import os
import re
import json
import yaml
import shutil
from datetime import datetime
from PyRSS2Gen import RSS2, RSSItem
from dateutil.parser import parse
from distutils.util import strtobool
from port.md2html import compile_markdown

meta_re = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
title_re = re.compile(r'^#\s?([^#\n]+)')


def build_site(conf):
    """
    Build a site based on the passed config
    """
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
        posts_by_category[cat] = sorted(posts_by_category[cat], key = lambda x: x[0]['published_at'], reverse=True)
    posts = sum(posts_by_category.values(), [])
    posts = sorted(posts, key = lambda x: x[0]['published_at'], reverse=True)

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


def compile_file(path):
    """
    Compile a markdown file.
    """
    with open(path, 'r') as f:
        raw = f.read()

    parts = path.split('/')
    category = parts[-2]
    slug = parts[-1].replace('.md', '')

    raw, meta = extract_metadata(raw)
    html = compile_markdown(raw)

    data = {
        'html': html,
        'slug': slug,
        'category': category,
        'url': '/{}/{}'.format(category, slug)
    }
    data.update(meta)


    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()

    # Lead with the published timestamp so the
    # built files are in the right order
    build_slug = '{0}{1}_{2}_{3}'.format('D' if meta['draft'] else '',
                                         meta['published_ts'],
                                         category,
                                         slug)
    return data, build_slug


def extract_metadata(raw):
    """
    Extract metadata from raw markdown content.
    Returns the content with metadata removed and the extracted metadata.
    """
    # Defaults
    meta = {
        'title': '',
        'published_at': datetime.now(),
        'draft': False
    }

    # Try to extract metadata, specified as YAML front matter
    meta_match = meta_re.search(raw)
    if meta_match is not None:
        meta_raw = meta_match.group(1)
        try:
            ext_meta = yaml.load(meta_raw)
            meta.update(ext_meta)

            # Remove the metadata before we compile
            raw = meta_re.sub('', raw).strip()
        except yaml.scanner.ScannerError:
            pass

    # Convert to bool if necessary
    if isinstance(meta['draft'], str):
        meta['draft'] = strtobool(meta['draft'])

    # Convert to timestamp if necessary
    if isinstance(meta['published_at'], str):
        meta['published_at'] = parse(meta['published_at'])
    meta['published_ts'] = int(meta['published_at'].timestamp())

    # Try to extract title
    title_match = title_re.search(raw)
    if title_match is not None:
        meta['title'] = title_match.group(1)
        meta['title_html'] = compile_markdown(meta['title'])

        # Remove the title before we compile
        raw = title_re.sub('', raw).strip()

    return raw, meta


def compile_rss(posts, conf, outpath):
    """
    Compile a list of Posts to the specified outpath.
    """
    items = [RSSItem(
        title=p['title'],
        link=os.path.join(conf['SITE_URL'], p['category'], p['slug']),
        description=p['html'],
        pubDate=p['published_at']
    ) for p in posts]

    rss = RSS2(
        title=conf['SITE_NAME'],
        link=conf['SITE_URL'],
        description=conf['SITE_DESC'],
        lastBuildDate=datetime.now(),
        items=items
    )

    rss.write_xml(open(outpath, 'w'))
