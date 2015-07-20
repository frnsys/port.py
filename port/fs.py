import os


class FileManager():
    """
    For interfacing with the file system,
    used to keep paths consistent
    """

    def __init__(self, site_dir):
        self.site_dir = os.path.expanduser(site_dir)
        self.build_dir = os.path.join(self.site_dir, '.build')
        self.rss_dir = os.path.join(self.build_dir, '.rss')
        self.asset_dir = os.path.join(self.site_dir, 'assets')
        self.index_dir = os.path.join(self.build_dir, '.searchindex')
        self.pages_dir = os.path.join(self.site_dir, 'pages')
        self.bpages_dir = os.path.join(self.build_dir, 'pages')

    def rss_path(self, category):
        """
        Path to compiled RSS files for category or 'all'
        """
        return os.path.join(self.rss_dir, '{}.xml'.format(category))

    def post_path(self, build_slug):
        """
        Path to a compiled post
        """
        return os.path.join(self.build_dir, build_slug + '.json')

    def page_path(self, build_slug):
        """
        Path to a compiled page
        """
        return os.path.join(self.bpages_dir, build_slug + '.json')

    def category_dir(self, category):
        """
        Path to a compiled category
        """
        return os.path.join(self.build_dir, category)

    def category_meta_path(self, category):
        """
        Path to compiled category meta
        """
        return os.path.join(self.build_dir, category, 'meta.json')

    def raw_category_meta_path(self, category):
        """
        Path to uncompiled category meta
        Returns None if no meta is specified
        """
        meta_path = os.path.join(self.site_dir, category, 'meta.yaml')
        if not os.path.exists(meta_path):
            return None
        return meta_path

    def raw_categories(self):
        """
        Uncompiled category names
        """
        return [c for c in os.listdir(self.site_dir)
                if os.path.isdir(os.path.join(self.site_dir, c))
                and c not in ['assets', 'pages']
                and not c.startswith('.')]

    def raw_for_category(self, category):
        """
        Paths for uncompiled posts for a category
        """
        path = os.path.join(self.site_dir, category)
        return [os.path.join(path, f) for f in os.listdir(path)
                                      if f.endswith('.md')]

    def posts_for_category(self, category):
        """
        Paths for compiled posts for a category
        """
        cat_dir = self.category_dir(category)
        return [os.path.join(cat_dir, f) for f in os.listdir(cat_dir)
                                         if f.endswith('.json')
                                         and f != 'meta.json'
                                         and not f.startswith('D')]

    def find_post(self, category, slug):
        """
        Find compiled post matching the category and slug
        """
        cat_dir = self.category_dir(category)

        # meh
        for f in os.listdir(cat_dir):
            # Exclude the file extension and the timestamp
            if f[0] == 'D':
                fslug = f[12:-5]
            else:
                fslug = f[11:-5]
            if slug == fslug:
                return os.path.join(cat_dir, f)

    def categories(self):
        """
        Compiled category slugs
        """
        return [c for c in os.listdir(self.build_dir)
                  if c != 'pages'
                  and not c.startswith('.')]

    def pages(self):
        """
        Compiled page slugs
        """
        return [f.replace('.json', '')[1:] for f in os.listdir(self.bpages_dir)
                                        if f.endswith('.json')
                                        and not f.startswith('D')]

    def raw_pages(self):
        """
        Uncompiled page files
        """
        return [os.path.join(self.pages_dir, f)
                for f in os.listdir(self.pages_dir)
                if f.endswith('.md')]

    def find_page(self, slug):
        """
        Find compiled page matching the slug
        """
        # meh
        for f in os.listdir(self.bpages_dir):
            # Exclude the file extension and the timestamp
            if f[0] == 'D':
                fslug = f[2:-5]
            else:
                fslug = f[1:-5]
            if slug == fslug:
                return os.path.join(self.bpages_dir, f)
