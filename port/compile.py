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
from port.models import Post
from port.fs import FileManager

meta_re = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
title_re = re.compile(r'^#\s?([^#\n]+)')



def build_site(conf):
    """
    Build a site based on the passed config
    """
    site_dir = conf['SITE_DIR']
    fm = FileManager(site_dir)

    # Get all files and compile
    posts_by_cat = {}
    categories = fm.raw_categories()
    for cat in categories:
        cat_posts = [Post(compile_file(f)) for f in fm.raw_for_category(cat)]
        posts_by_cat[cat] = sorted(cat_posts, key=lambda p: p.published_at, reverse=True)
    posts = sum(posts_by_cat.values(), [])
    posts = sorted(posts, key=lambda p: p.published_at, reverse=True)

    # Remove existing build
    if os.path.exists(fm.build_dir):
        shutil.rmtree(fm.build_dir)
    os.makedirs(fm.build_dir)

    # Make category folders
    for cat in categories:
        os.makedirs(fm.category_dir(cat))

    # Write files
    for p in posts:
        post_path = fm.post_path(p)
        json.dump(p._data, open(post_path, 'w'))

    # Write RSS files
    os.makedirs(fm.rss_dir)
    for cat in categories:
        new_posts = [p for p in posts_by_cat[cat] if not p.draft][:20]
        compile_rss(new_posts, conf, fm.rss_path(cat))

    new_posts = [p for p in posts if not p.draft][:20]
    compile_rss(new_posts, conf, fm.rss_path('rss'))


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
    data['build_slug'] = '{2}/{0}{1}_{3}'.format('D' if meta['draft'] else '',
                                                 meta['published_ts'],
                                                 category,
                                                 slug)
    return data


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
        title=p.title,
        link=os.path.join(conf['SITE_URL'], p.category.slug, p.slug),
        description=p.html,
        pubDate=p.published_at
    ) for p in posts]

    rss = RSS2(
        title=conf['SITE_NAME'],
        link=conf['SITE_URL'],
        description=conf['SITE_DESC'],
        lastBuildDate=datetime.now(),
        items=items
    )

    rss.write_xml(open(outpath, 'w'))
