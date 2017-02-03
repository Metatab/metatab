# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Classes to build a Metatab document
"""
from os.path import join

def declaration_path(name):
    """Return the path to an included declaration"""
    from os.path import dirname, join, exists
    import metatab.declarations
    from metatab.exc import IncludeError

    d = dirname(metatab.declarations.__file__)

    path = join(d,name)

    if not exists(path):
        path = join(d, name + '.csv')

    if not exists(path):
        raise IncludeError("No local declaration file for name '{}' ".format(name))

    return path


# From http://stackoverflow.com/a/295466
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.type(
    """
    import re
    import unicodedata
    from six import text_type
    value = text_type(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf8')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value


def flatten(d, sep='.'):
    """Flatten a data structure into tuples"""
    def _flatten(e, parent_key='', sep='.'):
        import collections

        prefix = parent_key+sep if parent_key else ''

        if isinstance(e, collections.MutableMapping):
            return tuple( (prefix+k2, v2) for k, v in e.items() for k2,v2 in _flatten(v,  k, sep ) )
        elif isinstance(e, collections.MutableSequence):
            return tuple( (prefix+k2, v2) for i, v in enumerate(e) for k2,v2 in _flatten(v,  str(i), sep ) )
        else:
            return (parent_key, (e,)),

    return tuple( (k, v[0]) for k, v in _flatten(d, '', sep) )

# From http://stackoverflow.com/a/2597440
class Bunch(object):
  def __init__(self, adict):
    self.__dict__.update(adict)

MP_DIR = '_metapack'
DOWNLOAD_DIR = join(MP_DIR,'download')
PACKAGE_DIR = join(MP_DIR,'package')
OLD_DIR = join(MP_DIR,'old')

def make_dir_structure(base_dir):
    """Make the build directory structure. """

    def maybe_makedir(*args):

        p = join(base_dir, *args)

        if exists(p) and not isdir(p):
            raise IOError("File '{}' exists but is not a directory ".format(p))

        if not exists(p):
            makedirs(p)

    maybe_makedir(DOWNLOAD_DIR)
    maybe_makedir(PACKAGE_DIR)
    maybe_makedir(OLD_DIR)

def make_metatab_file(template='metatab'):

    from os.path import join, dirname
    import metatab.templates
    from metatab.doc import MetatabDoc

    template_path = join(dirname(metatab.templates.__file__),template+'.csv')

    doc = MetatabDoc().load_csv(template_path)

    return doc

def scrape_urls_from_web_page(page_url):
    from bs4 import BeautifulSoup
    from six.moves.urllib.parse import urlparse, urlsplit, urlunsplit
    from six.moves.urllib.request import urlopen
    import os

    parts = list(urlsplit(page_url))

    parts[2] = ''
    root_url = urlunsplit(parts)

    html_page = urlopen(page_url)
    soup = BeautifulSoup(html_page, "lxml")

    d = dict(external_documentation={}, sources={}, links={})

    for link in soup.findAll('a'):

        if not link:
            continue

        if link.string:
            text = link.string
        else:
            text = None

        url = link.get('href')

        if not url:
            continue

        if 'javascript' in url:
            continue

        if url.startswith('http'):
            pass
        elif url.startswith('/'):
            url = os.path.join(root_url, url)
        else:
            url = os.path.join(page_url, url)

        base = os.path.basename(url)

        if '#' in base:
            continue

        try:
            fn, ext = base.split('.', 1)
        except ValueError:
            fn = base
            ext = ''

        # xlsm is a bug that adds 'm' to the end of the url. No idea.
        if ext.lower() in ('zip', 'csv', 'xls', 'xlsx', 'xlsm', 'txt'):
            d['sources'][fn] = dict(url=url, description=text)

        elif ext.lower() in ('pdf', 'html'):
            d['external_documentation'][fn] = dict(url=url, description=text)

        else:
            d['links'][text] = dict(url=url, description=text)

    return d

