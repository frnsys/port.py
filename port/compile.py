import os
import re
from time import time
from datetime import datetime
from PyRSS2Gen import RSS2, RSSItem
from dateutil.parser import parse
from distutils.util import strtobool
from port.md2html import compile_markdown

meta_re = re.compile(r'%~\n(.+)\n%~', re.DOTALL)
title_re = re.compile(r'#\s?(.+)')


def compile_file(path):
    """
    Compile a markdown file.
    """
    with open(path, 'r') as f:
        raw = f.read()

    parts = path.split('/')
    category = parts[-2]
    slug = parts[-1].replace('.md', '')

    raw, meta = extract_metadata(raw)
    html = compile_markdown(raw)

    data = {
        'html': html,
        'slug': slug,
        'category': category
    }
    data.update(meta)


    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()

    # Lead with the published timestamp so the
    # built files are in the right order
    build_slug = '{0}{1}_{2}_{3}'.format('D' if meta['draft'] else '',
                                         meta['published_ts'],
                                         category,
                                         slug)
    return data, build_slug


def extract_metadata(raw):
    """
    Extract metadata from raw markdown content.
    Returns the content with metadata removed and the extracted metadata.
    """
    # Defaults
    meta = {
        'title': '',
        'published_at': datetime.now(),
        'draft': False
    }

    # Try to extract metadata, demarcated by '%~'
    meta_match = meta_re.search(raw)
    if meta_match is not None:
        meta_raw = meta_match.group(1)
        ext_meta = dict([[i.strip() for i in l.split(':')] for l in meta_raw.split('\n')])
        meta.update(ext_meta)

        # Remove the metadata before we compile
        raw = meta_re.sub('', raw).strip()

    # Convert to bool if necessary
    if isinstance(meta['draft'], str):
        meta['draft'] = strtobool(meta['draft'])

    # Convert to timestamp if necessary
    if isinstance(meta['published_at'], str):
        meta['published_at'] = parse(meta['published_at'])
    meta['published_ts'] = int(meta['published_at'].timestamp())

    # Try to extract title
    title_match = title_re.search(raw)
    if title_match is not None:
        meta['title'] = title_match.group(1)
        meta['title_html'] = compile_markdown(meta['title'])

        # Remove the title before we compile
        raw = title_re.sub('', raw).strip()

    return raw, meta


def compile_rss(posts, conf, outpath):
    """
    Compile a list of Posts to the specified outpath.
    """
    items = [RSSItem(
        title=p['title'],
        link=os.path.join(conf['SITE_URL'], p['category'], p['slug']),
        description=p['html'],
        pubDate=p['published_at']
    ) for p in posts]

    rss = RSS2(
        title=conf['SITE_NAME'],
        link=conf['SITE_URL'],
        description=conf['SITE_DESC'],
        lastBuildDate=datetime.now(),
        items=items
    )

    rss.write_xml(open(outpath, 'w'))
