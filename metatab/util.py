# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Classes to build a Metatab document
"""
import logging
import os
import shutil
import sys
from genericpath import exists, isfile
from os import makedirs
from os.path import join, basename, dirname, isdir, abspath

#from rowgenerators import reparse_url, parse_url_to_dict, unparse_url_dict, Url

from metatab import DEFAULT_METATAB_FILE
from rowgenerators import get_cache


def declaration_path(name):
    """Return the path to an included declaration"""
    from os.path import dirname, join, exists
    import  metatabdecl
    from metatab.exc import IncludeError

    d = dirname(metatabdecl.__file__)

    path = join(d, name)

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
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf8').strip().lower()
    value = re.sub(r'[^\w\s\-\.]', '', value)
    value = re.sub(r'[-\s]+', '-', value)
    return value


def flatten(d, sep='.'):
    """Flatten a data structure into tuples"""

    def _flatten(e, parent_key='', sep='.'):
        import collections

        prefix = parent_key + sep if parent_key else ''

        if isinstance(e, collections.MutableMapping):
            return tuple((prefix + k2, v2) for k, v in e.items() for k2, v2 in _flatten(v, k, sep))
        elif isinstance(e, collections.MutableSequence):
            return tuple((prefix + k2, v2) for i, v in enumerate(e) for k2, v2 in _flatten(v, str(i), sep))
        else:
            return (parent_key, (e,)),

    return tuple((k, v[0]) for k, v in _flatten(d, '', sep))


# From http://stackoverflow.com/a/2597440
class Bunch(object):
    def __init__(self, adict):
        self.__dict__.update(adict)


MP_DIR = '_metapack'
DOWNLOAD_DIR = join(MP_DIR, 'download')
PACKAGE_DIR = join(MP_DIR, 'package')
OLD_DIR = join(MP_DIR, 'old')


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
    from os.path import dirname
    from rowgenerators.util import fs_join as join
    import metatab.templates
    from metatab.doc import MetatabDoc

    template_path = join(dirname(metatab.templates.__file__), template + '.csv')

    doc = MetatabDoc(template_path)

    return doc



import mimetypes

mimetypes.init()
mime_map = {v: k.strip('.') for k, v in mimetypes.types_map.items()}
mime_map['application/x-zip-compressed'] = 'zip'
mime_map['application/vnd.ms-excel'] = 'xls'
mime_map['text/html'] = 'html'


# From https://gist.github.com/zdavkeos/1098474
def walk_up(bottom):
    """  mimic os.walk, but walk 'up' instead of down the directory tree
    :param bottom:
    :return:
    """
    import os
    from os import path

    bottom = path.realpath(bottom)

    # get files in current dir
    try:
        names = os.listdir(bottom)
    except Exception as e:
        raise e

    dirs, nondirs = [], []
    for name in names:
        if path.isdir(path.join(bottom, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    yield bottom, dirs, nondirs

    new_path = path.realpath(path.join(bottom, '..'))

    # see if we are at the top
    if new_path == bottom:
        return

    for x in walk_up(new_path):
        yield x


def ensure_dir(path):
    if path and not exists(path):
        makedirs(path)


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


logger = logging.getLogger('user')
logger_err = logging.getLogger('cli-errors')
debug_logger = logging.getLogger('debug')


def cli_init(log_level=logging.INFO):
    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter('%(message)s'))
    out_hdlr.setLevel(log_level)
    logger.addHandler(out_hdlr)
    logger.setLevel(log_level)

    out_hdlr = logging.StreamHandler(sys.stderr)
    out_hdlr.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    out_hdlr.setLevel(logging.WARN)
    logger_err.addHandler(out_hdlr)
    logger_err.setLevel(logging.WARN)


def prt(*args, **kwargs):
    logger.info(' '.join(str(e) for e in args), **kwargs)


def warn(*args, **kwargs):
    logger_err.warn(' '.join(str(e) for e in args), **kwargs)


def err(*args, **kwargs):
    logger_err.critical(' '.join(str(e) for e in args), **kwargs)
    sys.exit(1)


def import_name_or_class(name):
    " Import an obect as either a fully qualified, dotted name, "

    if isinstance(name, str):

        # for "a.b.c.d" -> [ 'a.b.c', 'd' ]
        module_name, object_name = name.rsplit('.',1)
        # __import__ loads the multi-level of module, but returns
        # the top level, which we have to descend into
        mod = __import__(module_name)

        components = name.split('.')

        for comp in components[1:]: # Already got the top level, so start at 1

            mod = getattr(mod, comp)
        return mod
    else:
        return name # Assume it is already the thing we want to import
