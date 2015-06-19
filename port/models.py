import os
import re
import json
from flask import current_app
from dateutil.parser import parse

isodate_re = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(.\d{6})?$')


class Post():
    def __init__(self, data):
        for k, v in data.items():
            # Check if it's a isoformat datetime
            if isinstance(v, str) and isodate_re.search(v) is not None:
                v = parse(v)
            if k == 'category':
                v = Category(v)
            setattr(self, k, v)

    @classmethod
    def from_file(cls, path):
        data = json.load(open(path, 'r'))
        return cls(data)

    @classmethod
    def all(cls):
        categories = cls.categories()
        posts = sum([cls.for_category(c) for c in categories], [])
        return cls._sort(posts)

    @classmethod
    def for_category(cls, category):
        """
        Get posts for a category
        """
        cat_dir = current_app.fm.category_dir(category)
        posts = [Post.from_file(os.path.join(cat_dir, f)) for f in os.listdir(cat_dir)
                                                          if f.endswith('.json')
                                                          and not f.startswith('D')]
        return cls._sort(posts)

    @classmethod
    def single(cls, category, slug):
        """
        Get a single post
        """
        cat_dir = current_app.fm.category_dir(category)

        # meh
        for f in os.listdir(cat_dir):
            if slug in f:
                return Post.from_file(os.path.join(cat_dir, f))

    @classmethod
    def _sort(cls, posts):
        """
        Sort by reverse chron
        """
        # ugh
        return sorted(posts, key=lambda p: p.published_at, reverse=True)

    @classmethod
    def categories(cls):
        """
        Get a list of categories
        """
        build_dir = current_app.fm.build_dir
        return [c for c in os.listdir(build_dir)
                if c != 'rss']


class Meta():
    def __init__(self, request):
        conf = current_app.config
        build_dir = current_app.fm.build_dir
        for k, v in conf.items():
            setattr(self, k.lower(), v)

        self.categories = [Category(c) for c in os.listdir(build_dir)
                                       if c != 'rss']
        self.current_url = request.url


class Category():
    def __init__(self, slug):
        self.slug = slug
        self.name = slug.replace('_', ' ')
        self.url = '/{}'.format(slug)
