import os


class FileManager():
    """
    For interfacing with the file system,
    used to keep paths consistent
    """

    def __init__(self, site_dir):
        self.site_dir = site_dir
        self.build_dir = os.path.join(self.site_dir, '.build')
        self.rss_dir = os.path.join(self.build_dir, 'rss')
        self.asset_dir = os.path.join(self.site_dir, 'assets')

    def rss_path(self, category):
        return os.path.join(self.rss_dir, '{}.xml'.format(category))

    def post_path(self, post):
        return os.path.join(self.build_dir, post.build_slug + '.json')

    def category_dir(self, category):
        return os.path.join(self.build_dir, category)

    def raw_categories(self):
        return [c for c in os.listdir(self.site_dir)
                if os.path.isdir(os.path.join(self.site_dir, c))
                and c != 'assets'
                and not c.startswith('.')]

    def raw_for_category(self, category):
        path = os.path.join(self.site_dir, category)
        return [os.path.join(path, f) for f in os.listdir(path)
                                    if f.endswith('.md')]

    def posts_for_category(self, category):
        cat_dir = self.category_dir(category)
        return [os.path.join(cat_dir, f) for f in os.listdir(cat_dir)
                                         if f.endswith('.json')
                                         and not f.startswith('D')]

    def find_post(self, category, slug):
        cat_dir = self.category_dir(category)

        # meh
        for f in os.listdir(cat_dir):
            if slug in f:
                return os.path.join(cat_dir, f)

    def categories(self):
        return [c for c in os.listdir(self.build_dir)
                  if c != 'rss']
