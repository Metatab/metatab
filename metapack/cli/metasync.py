# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

import sys
from os import getcwd, makedirs, getenv
from os.path import join, basename, exists, dirname
from tabulate import tabulate
from metatab import _meta, DEFAULT_METATAB_FILE, resolve_package_metadata_url, MetatabDoc
from metatab.cli.core import prt, err, get_lib_module_dict, write_doc, datetime_now, \
    make_excel_package, make_s3_package, make_zip_package, make_filesystem_package, \
    update_name, metatab_info, PACKAGE_PREFIX, cli_init
from metatab.s3 import S3Bucket
from metatab.package import ZipPackage, ExcelPackage, FileSystemPackage, CsvPackage
from rowgenerators import Url, get_cache
from rowgenerators.util import clean_cache, join_url_path
from metatab.package import PackageError
from botocore.exceptions import NoCredentialsError


def metasync():
    import argparse

    cli_init()

    parser = argparse.ArgumentParser(
        prog='metasync',
        description='Create packages and store them in s3 buckets, version {}'.format(_meta.__version__),
    )

    parser.add_argument('-i', '--info', default=False, action='store_true',
                        help="Show configuration information")

    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help="For some command, be more verbose")

    parser.add_argument('-F', '--force', action='store_true', default=False,
                             help='Force building packages, even when they already exist')

    parser.add_argument('-p', '--profile', help="Name of a BOTO or AWS credentails profile", required=False)

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

    parser.add_argument('-C', '--credentials', help="Show S3 Credentials and exit. "
                                                    "Eval this string to setup credentials in other shells.",
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

    if m.args.credentials:
        show_credentials(m.args.profile)
        exit(0)

    if m.args.docker:
        run_docker(m)

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    if not m.args.s3:
        doc = MetatabDoc(m.mt_file)
        m.args.s3 = doc['Root'].find_first_value('Root.S3')

    if not m.args.s3:
        err("Must specify either -S or -s")

    if m.args.excel is not False or m.args.zip is not False or m.args.fs is not False:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    doc = MetatabDoc(m.mt_file)
    doc['Root'].get_or_new_term('Root.S3', m.args.s3)
    write_doc(doc, m.mt_file)

    # Update the Root.Distribution Term in the second stage metatab file.
    second_stage_mtfile, distupdated = update_distributions(m)

    if second_stage_mtfile != m.mt_file:
        prt("Building packages from: ", second_stage_mtfile)

    created = create_packages(m, second_stage_mtfile, distupdated=distupdated)

    prt("Synchronized these Package Urls")
    prt(tabulate(created))

    exit(0)


def show_credentials(profile):
    import boto3

    session = boto3.Session(profile_name=profile)

    if profile:
        cred_line = " 'eval $(metasync -C -p {} )'".format(profile)
    else:
        cred_line = " 'eval $(metasync -C)'"

    prt("export AWS_ACCESS_KEY_ID={} ".format(session.get_credentials().access_key))
    prt("export AWS_SECRET_ACCESS_KEY={}".format(session.get_credentials().secret_key))
    prt("# Run {} to configure credentials in a shell".format(cred_line))


def run_docker(m):
    """Re-run the metasync command in docker. """

    import botocore.session
    from subprocess import Popen, PIPE, STDOUT

    session = botocore.session.get_session()

    args = ['docker', 'run', '--rm', '-t', '-i',
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

    name = doc.find_first_value("Root.Name")

    for d in old_dists:

        if Url(d.value).resource_format == Url(v).resource_format and name not in d.value:
            try:
                doc.remove_term(d)
            except ValueError:
                pass

    t = doc.find_first('Root.Distribution', v)

    if not t:
        doc['Root'].new_term('Root.Distribution', v)

        return True
    else:
        return False


def update_distributions(m):
    """Add a distribution term for each of the distributions the sync is creating. Also updates the 'Issued' time"""

    doc = MetatabDoc(m.mt_file)

    access_value = doc.find_first_value('Root.Access')

    acl = 'private' if access_value == 'private' else 'public'

    b = S3Bucket(m.args.s3, acl=acl)

    updated = False

    old_dists = list(doc.find('Root.Distribution'))

    if m.args.fs is not False:
        p = FileSystemPackage(m.mt_file)
        if update_dist(doc, old_dists, b.access_url(p.save_path(), DEFAULT_METATAB_FILE)):
            prt("Added FS distribution to metadata")
            updated = True

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

    if m.args.csv is not False:

        p = CsvPackage(m.mt_file)
        url = b.access_url(basename(p.save_path()))
        if update_dist(doc, old_dists, url):
            prt("Added CSV distribution to metadata", url)
            updated = True


    t = doc['Root'].get_or_new_term('Root.Issued')
    t.value = datetime_now()

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


def create_packages(m, second_stage_mtfile, distupdated=None):
    """ Create Excel, ZIP, FS and CSV packages for upload to S3

    :param m: CLI Arguments object
    :param second_stage_mtfile: Path to a Metatab file, which must have distribution entries
    :param skip_if_exists: If True, don't recreate the file if exists.
    :return:
    """

    create_list = []
    url = None

    doc = MetatabDoc(second_stage_mtfile)

    access_value = doc.find_first_value('Root.Access')

    if access_value == 'private':
        acl = 'private'
    else:
        acl = 'public-read'

    # Only the first Filesystem nees an env; the others won't need to run processing, since they
    # are building from processed files.
    env = {}

    s3 = S3Bucket(m.args.s3, acl=acl, profile=m.args.profile)

    urls = []

    if (m.args.excel is not False or m.args.zip is not False or
            (hasattr(m.args, 'filesystem') and m.args.filesystem is not False)):
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    if m.args.force or distupdated is True:
        skip_if_exists = False
    else:
        skip_if_exists = True

    try:

        # Always create a filesystem package before ZIP or Excel, so we can use it as a source for
        # data for the other packages. This means that Transform processes and programs only need
        # to be run once.

        _, third_stage_mtfile, created = make_filesystem_package(second_stage_mtfile, m.cache, get_lib_module_dict(doc), skip_if_exists)

        if m.args.excel is not False:
            _, ex_url, created = make_excel_package(third_stage_mtfile, m.cache, env, skip_if_exists)
            with open(ex_url, mode='rb') as f:
                urls.append(('excel', s3.write(f.read(), basename(ex_url), acl)))

        if m.args.zip is not False:
            _, zip_url, created = make_zip_package(third_stage_mtfile, m.cache, env, skip_if_exists)
            with open(zip_url, mode='rb') as f:
                urls.append(('zip', s3.write(f.read(), basename(zip_url), acl)))

        # Note! This is a FileSystem package on the remote S3 bucket, not locally
        if m.args.fs is not False:
            try:
                fs_p, fs_url, created = make_s3_package(third_stage_mtfile, m.args.s3, m.cache, env, acl, skip_if_exists)
            except NoCredentialsError:
                print(getenv('AWS_SECRET_ACCESS_KEY'))
                err("Failed to find boto credentials for S3. "
                    "See http://boto3.readthedocs.io/en/latest/guide/configuration.html ")

            # A crappy hack. make_s3_package should return the correct url
            if access_value == 'private':
                urls.append(('fs', fs_p.private_access_url))
            else:
                urls.append(('fs', fs_p.public_access_url))

        # Make the CSV package from the filesystem package on S3; this will ensure that the
        # package's resource URLs point to the S3 objects
        if m.args.csv is not False:

            # Using the signed url in case the bucket is private
            p = CsvPackage(fs_p.access_url, cache=m.tmp_cache)
            csv_url = p.save(PACKAGE_PREFIX)
            with open(csv_url, mode='rb') as f:
                urls.append(('csv', s3.write(f.read(), basename(csv_url), acl)))

    except PackageError as e:
        err("Failed to generate package: {}".format(e))



    return urls
