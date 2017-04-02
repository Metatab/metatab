# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

import mimetypes
import sys
from os import getcwd
from os.path import join, basename

import six

from metatab import _meta, DEFAULT_METATAB_FILE, resolve_package_metadata_url, MetatabDoc
from metatab import open_package
from metatab.cli.core import prt, err, get_lib_module_dict, write_doc, datetime_now, \
    make_excel_package, make_filesystem_package, make_s3_package, make_zip_package, update_name, metatab_info, S3Bucket
from rowgenerators import get_cache, Url
from metatab.package import ZipPackage, ExcelPackage, FileSystemPackage, CsvPackage
from datetime import datetime

def metasync():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metasync',
        description='Create packages and store them in s3 buckets, version {}'.format(_meta.__version__),
    )

    parser.add_argument('-i', '--info', default=False, action='store_true',
                        help="Show configuration information")

    parser.add_argument('-s', '--s3', help="URL to S3 where packages will be stored", required=True)

    parser.add_argument('-e', '--excel', action='store_true', default=False,
                        help='Create an excel package from a metatab file and copy it to S3. ')

    parser.add_argument('-z', '--zip', action='store_true', default=False,
                        help='Create a zip package from a metatab file and copy it to S3. ')

    parser.add_argument('-c', '--csv', action='store_true', default=False,
                        help='Create a csv package from a metatab file and copy it to S3. Requires building a file system package')

    parser.add_argument('-f', '--fs', action='store_true', default=False,
                        help='Create a Filesystem package. Unlike -e and -f, only writes the package to S3.')

    parser.add_argument('metatabfile', nargs='?', help='Path to a Metatab file')

    class MetapackCliMemo(object):
        def __init__(self, args):
            self.cwd = getcwd()
            self.args = args
            self.cache = get_cache('metapack')

            self.mtfile_arg = args.metatabfile if args.metatabfile else join(self.cwd, DEFAULT_METATAB_FILE)

            self.mtfile_url = Url(self.mtfile_arg)
            self.resource = self.mtfile_url.parts.fragment

            self.package_url, self.mt_file = resolve_package_metadata_url(self.mtfile_url.rebuild_url(False, False))

            self.args.fs = self.args.csv or self.args.fs



    m = MetapackCliMemo(parser.parse_args(sys.argv[1:]))

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    if m.args.excel is not False or m.args.zip is not False or m.args.fs is not False:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    distupdated = update_distributions(m)

    created = create_packages(m, skip_if_exists= False if distupdated else True)

    exit(0)


def update_dist(doc, v):
    t = doc.find('Root.Distribution', v)

    if not t:
        doc['Root'].new_term('Root.Distribution', v)
        return True
    else:
        return False

def update_distributions(m):
    """Add a distribution term for each of the distributions the sync is creating. Also updates the 'Issued' time"""
    b = S3Bucket(m.args.s3)
    doc = MetatabDoc(m.mt_file)
    updated = False

    if m.args.excel is not False:
        p = ExcelPackage(m.mt_file)
        if update_dist(doc, b.access_url(p.save_path())):
            prt("Added Excel distribution to metadata")
            updated = True

    if m.args.zip is not False:
        p = ZipPackage(m.mt_file)
        if update_dist(doc, b.access_url(p.save_path())):
            prt("Added ZIP distribution to metadata")
            updated = True

    if m.args.fs is not False:
        p = FileSystemPackage(m.mt_file)
        if update_dist(doc, b.access_url(p.save_path(), DEFAULT_METATAB_FILE)):
            prt("Added FS distribution to metadata")
            updated = True

    if m.args.csv is not False:
        p = CsvPackage(m.mt_file)
        url = b.access_url(basename(p.save_path()))
        if update_dist(doc, url):
            prt("Added CSV distribution to metadata", url)
            updated = True

    doc['Root']['Issued'] = datetime_now()

    write_doc(doc, m.mt_file)

    return updated

def create_packages(m, skip_if_exists=False):
    from metatab.package import PackageError

    create_list = []
    url = None

    doc = MetatabDoc(m.mt_file)
    env = get_lib_module_dict(doc)

    s3 = S3Bucket(m.args.s3)

    try:

        if m.args.excel is not False:
            ex_url, created = make_excel_package(m.mt_file, m.cache, env, skip_if_exists)
            written_url = s3.write(ex_url, basename(ex_url))

        if m.args.zip is not False:
            zip_url, created = make_zip_package(m.mt_file, m.cache, env, skip_if_exists)
            written_url = s3.write(zip_url, basename(zip_url))

        if m.args.fs is not False:
            fs_url, created = make_s3_package(m.mt_file, m.args.s3, m.cache, env, skip_if_exists)

        if m.args.csv is not False:
            p = CsvPackage(join(fs_url, DEFAULT_METATAB_FILE))
            csv_url = p.save()
            written_url = s3.write(csv_url, basename(csv_url))

    except PackageError as e:
        err("Failed to generate package: {}".format(e))



