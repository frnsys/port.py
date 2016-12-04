import os
import re
import json
import yaml
import shutil
from datetime import datetime
from PyRSS2Gen import RSS2, RSSItem
from dateutil.parser import parse
from distutils.util import strtobool
from html.parser import HTMLParser
from nom.md2html import compile_markdown
from port.fs import FileManager

meta_re = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
title_re = re.compile(r'^#\s?([^#\n]+)')
md_img_re = re.compile(r'!\[.*?\]\(`?([^`\(\)]+)`?\)')


class HTMLCleaner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def remove_html(html):
    cleaner = HTMLCleaner()
    cleaner.feed(html)
    return cleaner.get_data()


def get_description(text, length=140):
    return text if len(text) <= 140 else text[:139] + '…'


def get_images(md):
    return [img for img in md_img_re.findall(md)]


def build_site(conf):
    """build a site based on the passed config"""
    site_dir = conf['SITE_DIR']
    fm = FileManager(site_dir)

    # get all posts and compile
    posts_by_cat = {}
    categories = fm.raw_categories()
    metas_by_cat = {}
    for cat in categories:
        cat_posts = [compile_post(f) for f in fm.raw_for_category(cat)]
        posts_by_cat[cat] = sorted(cat_posts, key=lambda p: p['published_at'], reverse=True)
        metas_by_cat[cat] = compile_category_meta(fm.raw_category_meta_path(cat))
    posts = sum(posts_by_cat.values(), [])
    posts = sorted(posts, key=lambda p: p['published_at'], reverse=True)

    # compile pages
    if os.path.exists(fm.pages_dir):
        pages = [compile_page(p) for p in fm.raw_pages()]
    else:
        pages = []

    # remove existing build
    if os.path.exists(fm.build_dir):
        shutil.rmtree(fm.build_dir)
    os.makedirs(fm.build_dir)

    # make category folders
    for cat in categories:
        os.makedirs(fm.category_dir(cat))

    # make pages folder
    os.makedirs(fm.bpages_dir)

    # write category meta files
    for cat, meta in metas_by_cat.items():
        meta_path = fm.category_meta_path(cat)
        json.dump(meta, open(meta_path, 'w'))

    # write post files
    for p in posts:
        post_path = fm.post_path(p['build_slug'])
        json.dump(p, open(post_path, 'w'))

    # write page files
    for p in pages:
        page_path = fm.page_path(p['build_slug'])
        json.dump(p, open(page_path, 'w'))

    # write RSS files
    os.makedirs(fm.rss_dir)
    for cat in categories:
        new_posts = [p for p in posts_by_cat[cat] if not p['draft']][:20]
        compile_rss(new_posts, conf, fm.rss_path(cat))

    new_posts = [p for p in posts if not p['draft']][:20]
    compile_rss(new_posts, conf, fm.rss_path('rss'))


def compile_post(path):
    """compile a markdown post"""
    with open(path, 'r') as f:
        raw = f.read()

    parts = path.split('/')
    category = parts[-2]
    slug = parts[-1].replace('.md', '')

    raw, meta = extract_metadata(raw)
    html = compile_markdown(raw)
    text = remove_html(html)
    desc = get_description(text)
    imgs = get_images(raw)

    data = {
        'plain': raw,
        'html': html,
        'text': text,
        'slug': slug,
        'description': desc,
        'category': category,
        'image': imgs[0] if imgs else None,
        'url': '/{}/{}'.format(category, slug)
    }
    data.update(meta)

    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()

    # lead with the published timestamp so the
    # built files are in the right order
    data['build_slug'] = '{2}/{0}{1}_{3}'.format(
        'D' if meta['draft'] else '',
        meta['published_ts'],
        category,
        slug)
    return data


def compile_page(path):
    """compile a markdown page"""
    with open(path, 'r') as f:
        raw = f.read()

    parts = path.split('/')
    slug = parts[-1].replace('.md', '')

    raw, meta = extract_metadata(raw)
    html = compile_markdown(raw)
    text = remove_html(html)
    desc = get_description(text)
    imgs = get_images(raw)

    data = {
        'plain': raw,
        'html': html,
        'text': text,
        'slug': slug,
        'description': desc,
        'url': '/{}'.format(slug),
        'image': imgs[0] if imgs else None
    }
    data.update(meta)

    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()

    # lead with the published timestamp so the
    # built files are in the right order
    data['build_slug'] = '{0}_{1}'.format(
        'D' if meta['draft'] else '', slug)
    return data


def compile_category_meta(path):
    """compile category meta file"""
    if path is None:
        return {}
    else:
        return yaml.load(open(path, 'r'))


def extract_metadata(raw):
    """extract metadata from raw markdown content;
    returns the content with metadata removed and the extracted metadata"""
    # defaults
    meta = {
        'title': '',
        'published_at': datetime.now(),
        'draft': False
    }

    # try to extract metadata, specified as YAML front matter
    meta_match = meta_re.search(raw)
    if meta_match is not None:
        meta_raw = meta_match.group(1)
        try:
            ext_meta = yaml.load(meta_raw)
            meta.update(ext_meta)

            # remove the metadata before we compile
            raw = meta_re.sub('', raw).strip()
        except yaml.scanner.ScannerError:
            pass

    # convert to bool if necessary
    if isinstance(meta['draft'], str):
        meta['draft'] = strtobool(meta['draft'])

    # convert to timestamp if necessary
    if isinstance(meta['published_at'], str):
        meta['published_at'] = parse(meta['published_at'])
    meta['published_ts'] = int(meta['published_at'].timestamp())

    # try to extract title
    title_match = title_re.search(raw)
    if title_match is not None:
        meta['title'] = title_match.group(1)
        meta['title_html'] = compile_markdown(meta['title'])

        # remove the title before we compile
        raw = title_re.sub('', raw).strip()

    return raw, meta


def compile_rss(posts, conf, outpath):
    """compile a list of posts to the specified outpath"""
    items = [RSSItem(
        title=p['title'],
        link=os.path.join(conf['SITE_URL'], p['category'], p['slug']),
        description=p['html'],
        pubDate=p['published_at']) for p in posts]

    rss = RSS2(
        title=conf['SITE_NAME'],
        link=conf['SITE_URL'],
        description=conf['SITE_DESC'],
        lastBuildDate=datetime.now(),
        items=items)

    rss.write_xml(open(outpath, 'w'))
