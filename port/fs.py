import os


class FileManager():
    """for interfacing with the file system,
    used to keep paths consistent"""

    def __init__(self, site_dir):
        self.site_dir = os.path.expanduser(site_dir)
        self.asset_dir = os.path.join(self.site_dir, 'assets')
        self.pages_dir = os.path.join(self.site_dir, 'pages')

    def category_meta(self, category):
        """path to uncompiled category meta;
        returns None if no meta is specified"""
        meta_path = os.path.join(self.site_dir, category, 'meta.yaml')
        if not os.path.exists(meta_path):
            return None
        return meta_path

    def categories(self):
        """uncompiled category names (recursive)"""
        cats = []
        queue = [self.site_dir]
        while queue:
            dir = queue.pop(0)
            has_md = False
            for d in os.listdir(dir):
                if d.endswith('.md'):
                    has_md = True

                if d in ['assets', 'pages'] or d.startswith('.'):
                    continue

                path = os.path.join(dir, d)
                if not os.path.isdir(path):
                    continue

                queue.append(path)

            if has_md:
                cats.append(dir)
        return [os.path.relpath(c, self.site_dir) for c in cats]

    def posts_for_category(self, category):
        """paths for uncompiled posts for a category"""
        path = os.path.join(self.site_dir, category)
        return [os.path.join(path, f) for f in os.listdir(path)
                                      if f.endswith('.md')]

    def pages(self):
        """uncompiled page files"""
        return [os.path.join(self.pages_dir, f)
                for f in os.listdir(self.pages_dir)
                if f.endswith('.md')]
