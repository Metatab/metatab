# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Support functions for the metapack program, for creating metatab data packages.

"""

from os import makedirs
from os.path import join, exists, isdir

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
    from metatab import MetatabDoc

    template_path = join(dirname(metatab.templates.__file__),template+'.csv')

    doc = MetatabDoc().load_csv(template_path)

    return doc
