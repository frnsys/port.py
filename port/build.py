import os
import re
import math
import yaml
import shutil
from datetime import datetime
from PyRSS2Gen import RSS2, RSSItem
from dateutil.parser import parse
from distutils.util import strtobool
from html.parser import HTMLParser
from nom.md2html import compile_markdown
from port.fs import FileManager
from jinja2 import Environment, FileSystemLoader

meta_re = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
title_re = re.compile(r'^#\s?([^#\n]+)')
md_img_re = re.compile(r'!\[.*?\]\(`?([^`\(\)]+)`?\)')


class Bunch():
    def __init__(self, **data):
        for k, v in data.items():
            setattr(self, k, v)


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


class Builder():
    def __init__(self, theme_dir, build_dir):
        self.build_dir = build_dir
        self.env = Environment(loader=FileSystemLoader(theme_dir))

    def render(self, tmpl, outpath, **data):
        tmpl = self.env.get_template(tmpl)
        html = tmpl.render(**data)
        path = os.path.join(self.build_dir, outpath)
        dirs = os.path.dirname(path)
        if dirs:
            os.makedirs(dirs, exist_ok=True)
        with open(path, 'w') as f:
            f.write(html)

    def copydir(self, base, dirname):
        try:
            shutil.copytree(
                os.path.join(base, dirname),
                os.path.join(self.build_dir, dirname))
        except FileNotFoundError:
            pass

    def copy(self, base, fname):
        try:
            shutil.copytree(
                os.path.join(base, fname),
                os.path.join(self.build_dir, fname))
        except FileNotFoundError:
            pass

    def symlink(self, base, name):
        try:
            os.symlink(
                os.path.join(base, name),
                os.path.join(self.build_dir, name))
        except FileNotFoundError:
            pass

    def pagination(self, posts, per_page, pattern='/p/{}'):
        if per_page == 0:
            yield posts, Bunch(current=1, next=None, prev=None)
        else:
            last_page = math.ceil(len(posts)/per_page)
            for page in range(last_page):
                n = per_page * page
                m = per_page * (page + 1)
                next, prev = None, None
                if page < last_page - 1:
                    next = pattern.format(page+2)
                if page > 0:
                    prev = pattern.format(page)
                yield posts[n:m], Bunch(current=page+1, next=next, prev=prev)


def build_site(conf, base):
    """build a site based on the passed config"""
    conf['PER_PAGE'] = int(conf.get('PER_PAGE'))
    site_dir = os.path.expanduser(conf['SITE_DIR'])
    theme_dir = os.path.join(base, 'themes', conf['THEME'])
    build_dir = os.path.join(site_dir, '.build')
    b = Builder(theme_dir, build_dir)
    fm = FileManager(site_dir)

    # clean existing build
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    for f in os.listdir(build_dir):
        path = os.path.join(build_dir, f)
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        else:
            shutil.rmtree(path)

    # build/copy over simple stuff
    b.render('404.html', '404.html', site_data=conf)
    b.symlink(site_dir, 'assets')
    b.copydir(theme_dir, 'css')
    b.copydir(theme_dir, 'js')
    b.copy(site_dir, 'favicon.ico')

    # compile posts and categories
    posts_by_cat = {}
    metas_by_cat = {}
    for cat in fm.categories():
        cat_meta = compile_category(cat, fm.category_meta(cat), conf)
        cat_posts = [compile_post(f, cat, cat_meta) for f in fm.posts_for_category(cat)]
        posts_by_cat[cat] = sorted(cat_posts, key=lambda p: p.published_at, reverse=True)
        metas_by_cat[cat] = cat_meta
    posts = sum(posts_by_cat.values(), [])
    posts = sorted(posts, key=lambda p: p.published_at, reverse=True)
    categories = metas_by_cat.values()

    # compile pages
    if os.path.exists(fm.pages_dir):
        pages = [compile_page(p) for p in fm.pages()]
    else:
        pages = []

    base_meta = {k.lower(): v for k, v in conf.items()}
    base_meta['pages'] = pages
    base_meta['categories'] = categories

    # build pages
    for page in pages:
        meta = Bunch(current_url=page.url, **base_meta)
        b.render(page.template, '{}/index.html'.format(page.slug), page=page, site_data=meta)

    # build posts and categories
    for cat, cat_posts in posts_by_cat.items():
        os.makedirs(os.path.join(build_dir, cat))
        cat = metas_by_cat[cat]
        for post in cat_posts:
            meta = Bunch(current_url=post.url, **base_meta)
            b.render('single.html',
                     '{}/{}/index.html'.format(cat.slug, post.slug),
                     post=post, site_data=meta)
        meta = Bunch(current_url=cat.url, **base_meta)
        cat_posts = [p for p in cat_posts if not p.draft]
        for page_posts, page in b.pagination(cat_posts, cat.per_page, pattern='/{}/p/{{}}'.format(cat.slug)):
            if page.current == 1:
                b.render(cat.template, '{}/index.html'.format(cat.slug),
                         posts=page_posts, page=page,
                         category=cat, site_data=meta)
            b.render(cat.template, '{}/p/{}/index.html'.format(cat.slug, page.current),
                        posts=page_posts, page=page,
                        category=cat, site_data=meta)

    # build index
    meta = Bunch(current_url='/', **base_meta)
    posts = [p for p in posts if not p.draft]
    for page_posts, page in b.pagination(posts, conf['PER_PAGE']):
        if page.current == 1:
            b.render('index.html', 'index.html',
                     posts=page_posts, page=page, site_data=meta)
        b.render('index.html', 'p/{}/index.html'.format(page.current),
                posts=page_posts, page=page, site_data=meta)

    # build RSS files
    rss_dir = os.path.join(build_dir, 'rss')
    os.makedirs(rss_dir)
    for cat in fm.categories():
        cat_cleaned = cat.replace('/', '.')
        rss_path = os.path.join(rss_dir, '{}.xml'.format(cat_cleaned))
        new_posts = [p for p in posts_by_cat[cat] if not p.draft][:20]
        compile_rss(new_posts, conf, rss_path)

    rss_path = os.path.join(rss_dir, 'rss.xml')
    new_posts = [p for p in posts if not p.draft][:20]
    compile_rss(new_posts, conf, rss_path)


def compile_post(path, category, cat_meta):
    """compile a markdown post"""
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
        'category': cat_meta,
        'image': imgs[0] if imgs else None,
        'url': '/{}/{}'.format(category, slug)
    }
    data.update(meta)

    return Bunch(**data)


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
        'template': 'page.html',
        'url': '/{}'.format(slug),
        'image': imgs[0] if imgs else None
    }
    data.update(meta)

    return Bunch(**data)


def compile_category(slug, path, conf):
    """compile category data"""
    meta = {
        'slug': slug,
        'url': '/{}'.format(slug),
        'template': 'category.html',
        'per_page': conf['PER_PAGE'],
        'name': slug.replace('_', ' ')
    }
    if path is not None:
        data = yaml.safe_load(open(path, 'r'))
        meta.update(data)
    return Bunch(**meta)


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
            ext_meta = yaml.safe_load(meta_raw)
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

def unabsolute_urls(html, conf):
    html = html.replace('src="/', 'src="{}/'.format(conf['SITE_URL']))
    html = html.replace('href="/', 'href="{}/'.format(conf['SITE_URL']))
    return html

def compile_rss(posts, conf, outpath):
    """compile a list of posts to the specified outpath"""
    items = [RSSItem(
        title=p.title,
        link=os.path.join(conf['SITE_URL'], p.category.slug, p.slug),
        description=unabsolute_urls(p.html, conf),
        pubDate=p.published_at) for p in posts]

    rss = RSS2(
        title=conf['SITE_NAME'],
        link=conf['SITE_URL'],
        description=conf['SITE_DESC'],
        lastBuildDate=datetime.now(),
        items=items)

    rss.write_xml(open(outpath, 'w'))
