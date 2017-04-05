# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

import sys
from os import getcwd, makedirs
from os.path import join, basename, exists, dirname
from tabulate import tabulate
from metatab import _meta, DEFAULT_METATAB_FILE, resolve_package_metadata_url, MetatabDoc
from metatab.cli.core import prt, err, get_lib_module_dict, write_doc, datetime_now, \
    make_excel_package, make_s3_package, make_zip_package, update_name, metatab_info, \
    S3Bucket, PACKAGE_PREFIX
from metatab.package import ZipPackage, ExcelPackage, FileSystemPackage, CsvPackage
from rowgenerators import  Url, get_cache
from rowgenerators.util import clean_cache


def metasync():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metasync',
        description='Create packages and store them in s3 buckets, version {}'.format(_meta.__version__),
    )

    parser.add_argument('-i', '--info', default=False, action='store_true',
                        help="Show configuration information")

    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help="For some command, be more verbose")

    parser.add_argument('-s', '--s3', help="URL to S3 where packages will be stored", required=False)

    parser.add_argument('-S', '--all-s3', help="Synonym for `metasync -c -e -f -z -s <url>`", required=False)

    parser.add_argument('-e', '--excel', action='store_true', default=False,
                        help='Create an excel package from a metatab file and copy it to S3. ')

    parser.add_argument('-z', '--zip', action='store_true', default=False,
                        help='Create a zip package from a metatab file and copy it to S3. ')

    parser.add_argument('-c', '--csv', action='store_true', default=False,
                        help='Create a csv package from a metatab file and copy it to S3. Requires building a file system package')

    parser.add_argument('-f', '--fs', action='store_true', default=False,
                        help='Create a Filesystem package. Unlike -e and -f, only writes the package to S3.')

    parser.add_argument('-D', '--docker', help="Re-run the metasync command through docker",
                        action='store_true', default=False)

    parser.add_argument('metatabfile', nargs='?', help='Path to a Metatab file')

    class MetapackCliMemo(object):
        def __init__(self, raw_args):

            self.cwd = getcwd()

            self.raw_args = raw_args

            self.args = parser.parse_args(self.raw_args[1:])

            self.cache = get_cache('metapack')

            # This one is for loading packages that have just been
            # written to S3.
            self.tmp_cache = get_cache('temp')
            clean_cache(self.tmp_cache)

            if not self.args.all_s3 and not self.args.s3:
                err("Must specify either -S or -s")

            if self.args.all_s3:
                self.args.s3 = self.args.all_s3
                self.args.excel = True
                self.args.zip = True
                self.args.csv = True
                self.args.fs = True

            self.mtfile_arg = self.args.metatabfile if self.args.metatabfile else join(self.cwd, DEFAULT_METATAB_FILE)

            self.mtfile_url = Url(self.mtfile_arg)
            self.resource = self.mtfile_url.parts.fragment

            self.package_url, self.mt_file = resolve_package_metadata_url(self.mtfile_url.rebuild_url(False, False))

            self.args.fs = self.args.csv or self.args.fs

    m = MetapackCliMemo(sys.argv)

    if m.args.docker:
        run_docker(m)

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    if m.args.excel is not False or m.args.zip is not False or m.args.fs is not False:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    second_stage_mtfile, distupdated = update_distributions(m)

    if second_stage_mtfile != m.mt_file:
        prt("Building packages from: ", second_stage_mtfile)

    created = create_packages(m, second_stage_mtfile, skip_if_exists= False if distupdated else True)

    prt("Synchronized these Package Urls")
    prt(tabulate(created))

    exit(0)

def run_docker(m):
    """Re-run the metasync command in docker. """

    import botocore.session
    from subprocess import Popen, PIPE, STDOUT

    session = botocore.session.get_session()

    args = ['docker', 'run','--rm','-t','-i',
            '-eAWS_ACCESS_KEY_ID={}'.format(session.get_credentials().access_key),
            '-eAWS_SECRET_ACCESS_KEY={}'.format(session.get_credentials().secret_key),
            'civicknowledge/metatab',
            'metasync']

    for a in ('-D', '--docker'):
        try:
            m.raw_args.remove(a)
        except ValueError:
            pass

    args.extend(m.raw_args[1:])

    if m.args.verbose:
        prt("Running Docker Command: ", ' '.join(args))
    else:
        prt("Running In Docker")

    process = Popen(args, stdout=PIPE, stderr=STDOUT)
    with process.stdout:
        for line in iter(process.stdout.readline, b''):
            prt(line.decode('ascii'), end='')

    exitcode = process.wait()  # 0 means success

    exit(exitcode)


def update_dist(doc, old_dists, v):

    # This isn't quite correct, because it will try to remove the .csv format
    # Distributions twice, since both <name>.csv and <name>/metadata.csv have the same format.
    # (That's why theres a try/except ) But, it is effective
    for d in old_dists:
        if Url(d.value).resource_format == Url(v).resource_format:
            try:
                doc.remove_term(d)
            except ValueError:
                pass

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

    old_dists = list(doc.find('Root.Distribution'))

    if m.args.excel is not False:
        p = ExcelPackage(m.mt_file)

        if update_dist(doc, old_dists, b.access_url(p.save_path())):
            prt("Added Excel distribution to metadata")
            updated = True

    if m.args.zip is not False:
        p = ZipPackage(m.mt_file)
        if update_dist(doc, old_dists, b.access_url(p.save_path())):
            prt("Added ZIP distribution to metadata")
            updated = True

    if m.args.fs is not False:
        p = FileSystemPackage(m.mt_file)
        if update_dist(doc, old_dists, b.access_url(p.save_path(), DEFAULT_METATAB_FILE)):
            prt("Added FS distribution to metadata")
            updated = True

    if m.args.csv is not False:
        p = CsvPackage(m.mt_file)
        url = b.access_url(basename(p.save_path()))
        if update_dist(doc, old_dists, url):
            prt("Added CSV distribution to metadata", url)
            updated = True

    doc['Root']['Issued'] = datetime_now()

    for d in doc.find('Root.Distribution'):
        print("XXX", d)


    if not write_doc(doc, m.mt_file):
        # The mt_file is probably a URL, so we can't write back to it,
        # but we need the updated distributions, so write it elsewhere, then
        # reload it in the next stage.
        second_stage_file = join(PACKAGE_PREFIX, DEFAULT_METATAB_FILE)

        if not exists(dirname(second_stage_file)):
            makedirs(dirname(second_stage_file))

        assert write_doc(doc, second_stage_file)

    else:
        second_stage_file = m.mt_file

    return second_stage_file, updated

from .core import PACKAGE_PREFIX

def create_packages(m, second_stage_mtfile, skip_if_exists=False):
    from metatab.package import PackageError

    create_list = []
    url = None

    doc = MetatabDoc(second_stage_mtfile)
    env = get_lib_module_dict(doc)

    s3 = S3Bucket(m.args.s3)

    urls = []

    try:

        if m.args.excel is not False:
            ex_url, created = make_excel_package(second_stage_mtfile, m.cache, env, skip_if_exists)
            urls.append(('excel',s3.write(ex_url, basename(ex_url))))

        if m.args.zip is not False:
            zip_url, created = make_zip_package(second_stage_mtfile, m.cache, env, skip_if_exists)
            urls.append(('zip',s3.write(zip_url, basename(zip_url))))

        if m.args.fs is not False:
            fs_url, created = make_s3_package(second_stage_mtfile, m.args.s3, m.cache, env, skip_if_exists)
            urls.append(('fs',fs_url))

        if m.args.csv is not False:
            p = CsvPackage(join(fs_url, DEFAULT_METATAB_FILE), cache=m.tmp_cache)
            csv_url = p.save(PACKAGE_PREFIX)
            urls.append(('csv',s3.write(csv_url, basename(csv_url))))

    except PackageError as e:
        err("Failed to generate package: {}".format(e))

    return urls



