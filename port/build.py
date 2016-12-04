import re
import os
import math
import json
import shutil
from port.fs import FileManager
from jinja2 import Environment, FileSystemLoader
from dateutil.parser import parse

isodate_re = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(.\d{6})?$')


class Category():
    def __init__(self, slug, data):
        for k, v in data.items():
            setattr(self, k.lower(), v)

        self.slug = slug
        self.url = '/{}'.format(slug)

        if not hasattr(self, 'name'):
            self.name = slug.replace('_', ' ')


class Post():
    def __init__(self, data):
        for k, v in data.items():
            # check if it's a isoformat datetime
            if isinstance(v, str) and isodate_re.search(v) is not None:
                v = parse(v)
            setattr(self, k.lower(), v)

    @classmethod
    def _sort(cls, posts):
        """sort by reverse chron"""
        return sorted(posts, key=lambda p: p.published_at, reverse=True)


class Page():
    def __init__(self, slug, data):
        for k, v in data.items():
            setattr(self, k.lower(), v)

        self.slug = slug
        self.url = '/{}'.format(slug)
        self.template = data.get('template', 'page.html')


class Builder():
    def __init__(self, fm, theme_dir, build_dir):
        self.fm = fm
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

    def category(self, slug):
        # load category meta data
        meta_path = self.fm.category_meta_path(slug)
        meta = json.load(open(meta_path, 'r'))
        return Category(slug, meta)

    def post(self, data):
        post = Post(data)
        post.category = self.category(data['category'])
        return post

    def page(self, fname, slug):
        data = json.load(open(fname, 'r'))
        return Page(slug, data)

    def pagination(self, posts, per_page):
        if per_page == 0:
            yield posts, 0, 0
        else:
            last_page = math.ceil(len(posts)/per_page)
            for page in range(last_page):
                n = per_page * page
                m = per_page * (page + 1)
                yield posts[n:m], page, last_page

    def copydir(self, base, dirname):
        try:
            shutil.copytree(
                os.path.join(base, dirname),
                os.path.join(self.build_dir, dirname))
        except FileNotFoundError:
            pass


def build(conf, base):
    site_dir = os.path.expanduser(conf['SITE_DIR'])
    theme_dir = os.path.join(base, 'themes', conf['THEME'])
    fm = FileManager(site_dir)

    # prep build dir
    build_dir = os.path.join(site_dir, '.site')
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.mkdir(build_dir)

    b = Builder(fm, theme_dir, build_dir)
    b.render('404.html', '404.html', site_data=conf)

    b.copydir(site_dir, 'assets')
    b.copydir(theme_dir, 'css')
    b.copydir(theme_dir, 'js')

    # TODO better catch/check
    try:
        shutil.copy(
            os.path.join(site_dir, 'assets/favicon.ico'),
            os.path.join(build_dir, 'favicon.ico'))
    except:
        pass

    # RSS
    categories = fm.categories()
    rss_dir = os.path.join(build_dir, 'rss')
    os.mkdir(rss_dir)
    shutil.copyfile(os.path.join(fm.rss_dir, 'rss.xml'), os.path.join(rss_dir, 'rss.xml'))
    for cat_slug in categories:
        shutil.copyfile(os.path.join(fm.rss_dir, '{}.xml'.format(cat_slug)), os.path.join(rss_dir, '{}.xml'.format(cat_slug)))

    meta_ = {k.lower(): v for k, v in conf.items()}
    meta_['categories'] = [b.category(c) for c in fm.categories()]
    meta_['pages'] = [b.page(fname, slug) for fname, slug in fm.pages()]

    # pages
    for fname, slug in fm.pages(drafts=True):
        meta = meta_.copy()
        meta['current_url'] = '/{}'.format(slug)
        page = b.page(fname, slug)
        b.render(page.template, '{}/index.html'.format(slug), page=page, site_data=meta)

    # posts & categories
    all_posts = []
    for slug in fm.categories():
        posts = []
        cat = b.category(slug)
        per_page = cat.per_page if hasattr(cat, 'per_page') else int(conf.get('PER_PAGE'))
        template = cat.template if hasattr(cat, 'template') else 'category.html'
        for fname in fm.posts_for_category(slug, drafts=True):
            data = json.load(open(fname, 'r'))
            post = b.post(data)
            meta = meta_.copy()
            meta['current_url'] = '/{}/{}'.format(slug, post.slug)
            b.render('single.html',
                     '{}/{}/index.html'.format(slug, post.slug),
                     post=post, site_data=meta)
            if not post.draft:
                posts.append(post)
                all_posts.append(post)

        # category index
        meta = meta_.copy()
        meta['current_url'] = '/{}'.format(slug)
        for posts_, page, last_page in b.pagination(posts, per_page):
            if page == 0:
                b.render(template,
                            '{}/index.html'.format(slug),
                            posts=posts_,
                            page=page+1,
                            category=cat,
                            last_page=last_page,
                            site_data=meta)
            b.render(template,
                        '{}/{}/index.html'.format(slug, page+1),
                        posts=posts_,
                        page=page+1,
                        category=cat,
                        last_page=last_page,
                        site_data=meta)

    # index
    per_page = int(conf.get('PER_PAGE'))
    for posts_, page, last_page in b.pagination(all_posts, per_page):
        if page == 0:
            b.render('index.html',
                        'index.html',
                        posts=posts_,
                        page=page+1,
                        last_page=last_page,
                        site_data=meta)
        b.render('index.html',
                    '{}/index.html'.format(page+1),
                    posts=posts_,
                    page=page+1,
                    last_page=last_page,
                    site_data=meta)
