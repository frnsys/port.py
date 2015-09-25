import os
import re
from datetime import datetime
from flask import current_app, request
from port.compile import build_site
from port.models import Post, Page, Meta, Category


punct = r'[ !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+'

cat_template = '''
name: {}
'''

post_template = '''
---
published_at: {published}
draft: {draft}
---

# {title}

{body}
'''


def slugify(text, delim='_'):
    """
    Simple slugifier
    """
    for p in punct:
        text = text.strip(p)
    return re.sub(punct, delim, text.lower())


def post_path(category, slug):
    return os.path.join(current_app.fm.site_dir,
                        category,
                        '{}.md'.format(slug))


def write_post(category, slug, published, draft, title, body):
    ppath = post_path(category, slug)
    published = published.strftime("%m.%d.%Y %H:%M")
    content = post_template.format(published=published,
                                   draft=draft,
                                   title=title,
                                   body=body).strip()
    with open(ppath, 'w') as f:
        f.write(content)
    build_site(current_app.config)


def move_post(from_cat, from_slug, to_cat, to_slug):
    ppath = post_path(from_cat, from_slug)
    ppath_ = post_path(to_cat, to_slug)

    if ppath == ppath_:
        return False

    os.rename(ppath, ppath_)
    build_site(current_app.config)
    return True


def trash_post(category, slug):
    # just in case, don't actually delete the file...
    trash_dir = os.path.join(current_app.fm.site_dir, '.trash')
    if not os.path.exists(trash_dir):
        os.makedirs(trash_dir)
    ppath = post_path(category, slug)
    trashed_post_path = os.path.join(trash_dir,
                                     '{}__{}.md'.format(slug,
                                                        datetime.now().strftime('%m_%d_%Y_%H_%M')))
    os.rename(ppath, trashed_post_path)
    build_site(current_app.config)


def make_category(name):
    cat_slug = slugify(name)
    cat_dir = os.path.join(current_app.fm.site_dir, cat_slug)
    os.makedirs(cat_dir)
    with open(os.path.join(cat_dir, 'meta.yaml'), 'w') as f:
        f.write(cat_template.format(name).strip())
    build_site(current_app.config)


def move_category(from_slug, to_name):
    to_slug = slugify(to_name)
    from_dir = os.path.join(current_app.fm.site_dir, from_slug)
    to_dir = os.path.join(current_app.fm.site_dir, to_slug)
    with open(os.path.join(from_dir, 'meta.yaml'), 'w') as f:
        f.write(cat_template.format(to_name).strip())
    os.rename(from_dir, to_dir)
    build_site(current_app.config)
    return to_slug


def single_post(category, slug):
    if category == 'pages':
        post = Page(slug)
        post.category = Pages()
    else:
        post = Post.single(category, slug)
    return post


def category_for_slug(slug):
    return Pages() if slug == 'pages' else Category(Slug)


def posts_for_category(category):
    """
    Custom method for getting compiled posts for a category
    so we can also get drafts
    """
    if category == 'pages':
        return pages()

    else:
        cat_dir = current_app.fm.category_dir(category)
        files =  [os.path.join(cat_dir, f) for f in os.listdir(cat_dir)
                                        if f.endswith('.json')
                                        and f != 'meta.json']
        posts = [Post.from_file(f) for f in files]
        return Post._sort(posts)



def pages():
    """
    Custom method for getting compiled pages, so we can also get drafts
    """
    raw_slugs = [f.replace('.json', '') for f in os.listdir(current_app.fm.bpages_dir)
                                        if f.endswith('.json')]
    slugs = [slug[2:] if slug[0] == 'D' else slug[1:] for slug in raw_slugs]

    ps = []
    for s in slugs:
        p = Page(s)

        # add a pseudo-category to keep things consistent
        p.category = Pages()
        ps.append(p)
    return ps


def categories():
    return Meta(request).categories + [Pages()]


class Pages():
    """
    A pseudo-category so that pages can be treated like regular posts
    """
    def __init__(self):
        self.name = 'Pages'
        self.slug = 'pages'


