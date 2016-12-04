import os


class FileManager():
    """for interfacing with the file system,
    used to keep paths consistent"""

    def __init__(self, site_dir):
        self.site_dir = os.path.expanduser(site_dir)
        self.build_dir = os.path.join(self.site_dir, '.build')
        self.rss_dir = os.path.join(self.build_dir, 'rss')
        self.asset_dir = os.path.join(self.site_dir, 'assets')
        self.pages_dir = os.path.join(self.site_dir, 'pages')

    def rss_path(self, category):
        """rath to compiled RSS files for category or 'all'"""
        return os.path.join(self.rss_dir, '{}.xml'.format(category))

    def category_dir(self, category):
        """path to a compiled category"""
        return os.path.join(self.build_dir, category)

    def raw_category_meta_path(self, category):
        """path to uncompiled category meta;
        returns None if no meta is specified"""
        meta_path = os.path.join(self.site_dir, category, 'meta.yaml')
        if not os.path.exists(meta_path):
            return None
        return meta_path

    def raw_categories(self):
        """uncompiled category names"""
        return [c for c in os.listdir(self.site_dir)
                if os.path.isdir(os.path.join(self.site_dir, c))
                and c not in ['assets', 'pages']
                and not c.startswith('.')]

    def raw_for_category(self, category):
        """paths for uncompiled posts for a category"""
        path = os.path.join(self.site_dir, category)
        return [os.path.join(path, f) for f in os.listdir(path)
                                      if f.endswith('.md')]

    def posts_for_category(self, category, drafts=False):
        """paths for compiled posts for a category"""
        cat_dir = self.category_dir(category)
        return [os.path.join(cat_dir, f) for f in os.listdir(cat_dir)
                                         if f.endswith('.json')
                                         and f != 'meta.json'
                                         and (not f.startswith('D') or drafts)]

    def raw_pages(self):
        """uncompiled page files"""
        return [os.path.join(self.pages_dir, f)
                for f in os.listdir(self.pages_dir)
                if f.endswith('.md')]
