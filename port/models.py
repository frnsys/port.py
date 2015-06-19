import os
import re
import json
from dateutil.parser import parse

isodate_re = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(.\d{6})?$')


class Post():
    def __init__(self, path):
        data = json.load(open(path, 'r'))

        for k, v in data.items():
            # Check if it's a isoformat datetime
            if isinstance(v, str) and isodate_re.search(v) is not None:
                v = parse(v)
            if k == 'category':
                v = Category(v)
            setattr(self, k, v)


class Meta():
    def __init__(self, conf, request):
        for k, v in conf.items():
            setattr(self, k.lower(), v)

        self.categories = [Category(c) for c in os.listdir(conf['SITE_DIR'])
                                       if c not in ['.build', 'assets']]
        self.current_url = request.url


class Category():
    def __init__(self, slug):
        self.slug = slug
        self.name = slug.replace('_', ' ')
        self.url = '/{}'.format(slug)
