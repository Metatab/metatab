# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

from os import getcwd, makedirs, getenv
from os.path import basename, dirname, exists

from botocore.exceptions import  NoCredentialsError
from tabulate import tabulate

from appurl import parse_app_url
from metapack import MetapackDoc, MetapackUrl
from metapack import MetapackPackageUrl
from metapack.cli.core import prt, err, metatab_info, get_lib_module_dict, write_doc, datetime_now, \
    make_filesystem_package, make_zip_package, make_s3_package, make_excel_package, update_name, \
    cli_init, update_dist
from metapack.exc import  PackageError
from metapack.package import *
from metapack.package.s3 import S3Bucket
from metatab import _meta, DEFAULT_METATAB_FILE
from rowgenerators.util import clean_cache
from rowgenerators.util import fs_join as join


class MetapackCliMemo(object):

    def __init__(self, args):
        from appurl import get_cache
        self.cwd = getcwd()

        self.args = args

        self.downloader = Downloader()

        self.cache = self.downloader.cache

        # This one is for loading packages that have just been
        # written to S3.
        self.tmp_cache = get_cache('temp')
        clean_cache(self.tmp_cache)

        if self.args.all_s3:
            self.args.s3 = self.args.all_s3
            self.args.excel = True
            self.args.zip = True
            self.args.zip = True
            self.args.csv = True
            self.args.fs = True

        if not self.args.s3:
            err("Must specify either -S or -s")

        self.mtfile_arg = self.args.metatabfile if self.args.metatabfile else join(self.cwd, DEFAULT_METATAB_FILE)

        self.mtfile_url = MetapackUrl(self.mtfile_arg, downloader=self.downloader)

        self.resource = self.mtfile_url.fragment

        self.package_url = self.mtfile_url.package_url
        self.mt_file = self.mtfile_url.metadata_url

        self.package_root = self.package_url.join(PACKAGE_PREFIX)

        if not self.args.s3:
            doc = MetapackDoc(self.mt_file)
            self.args.s3 = doc['Root'].find_first_value('Root.S3')

        self.s3_url = parse_app_url(self.args.s3)

        if not self.s3_url.scheme == 's3':
            self.s3_url = parse_app_url("s3://{}".format(self.args.s3))

        assert self.package_root._downloader

        self.args.fs = self.args.csv or self.args.fs

def metas3(subparsers):

    parser = subparsers.add_parser(
        's3',
        help='Create packages and store them in s3 buckets, version {}'.format(_meta.__version__),
    )

    parser.set_defaults(run_command=run_s3)

    parser.add_argument('-i', '--info', default=False, action='store_true',
                        help="Show configuration information")

    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help="For some command, be more verbose")

    parser.add_argument('-F', '--force', action='store_true', default=False,
                             help='Force building packages, even when they already exist')

    parser.add_argument('-p', '--profile', help="Name of a BOTO or AWS credentails profile", required=False)

    parser.add_argument('-s', '--s3', help="URL to S3 where packages will be stored", required=False)

    parser.add_argument('-S', '--all-s3', help="Synonym for `metasync -c -e -f -z -s <url>`", required=False)

    parser.add_argument('-d', '--distributions', help="Only update the distributions, don't send to S3",
                        action='store_true', required=False)

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


def run_s3(args):

    m = MetapackCliMemo(args)

    if m.args.credentials:
        show_credentials(m.args.profile)
        exit(0)

    if m.args.docker:
        run_docker(m)

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    if m.args.excel is not False or m.args.zip is not False or m.args.fs is not False:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    doc = MetapackDoc(m.mt_file)
    doc['Root'].get_or_new_term('Root.S3').value =  str(m.s3_url)

    write_doc(doc, m.mt_file)

    # Update the Root.Distribution Term in the second stage metatab file.
    second_stage_mtfile, distupdated = update_distributions(m)

    if not m.args.distributions:

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

    raise NotImplementedError("No longer have access to raw_args")

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


def update_distributions(m):
    """Add a distribution term for each of the distributions the sync is creating. Also updates the 'Issued' time"""

    doc = MetapackDoc(m.mt_file)

    # Clear out all of the old distributions
    for d in doc.find('Root.Distribution'):
        try:
            doc.remove_term(d)
        except ValueError:
            pass

    access_value = doc.find_first_value('Root.Access')

    acl = 'private' if access_value == 'private' else 'public'

    b = S3Bucket(m.s3_url, acl=acl)

    updated = False

    old_dists = list(doc.find('Root.Distribution'))

    if m.args.fs is not False:
        p = FileSystemPackageBuilder(m.mt_file, m.package_root)
        au = b.access_url(p.cache_path)
        if update_dist(doc, old_dists,au ):
            prt("Added FS distribution ", au)
            updated = True

    if m.args.excel is not False:
        p = ExcelPackageBuilder(m.mt_file, m.package_root)
        au = b.access_url(p.cache_path)
        if update_dist(doc, old_dists, au):
            prt("Added Excel distribution ", au)
            updated = True

    if m.args.zip is not False:
        p = ZipPackageBuilder(m.mt_file, m.package_root)
        au = b.access_url(p.cache_path)
        if update_dist(doc, old_dists, au):
            prt("Added ZIP distribution ", au)
            updated = True

    if m.args.csv is not False:

        p = CsvPackageBuilder(m.mt_file, m.package_root)
        au = b.access_url(basename(p.cache_path))
        if update_dist(doc, old_dists, au):
            prt("Added CSV distribution ", au)
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

    doc = MetapackDoc(second_stage_mtfile)

    access_value = doc.find_first_value('Root.Access')

    if access_value == 'private':
        acl = 'private'
    else:
        acl = 'public-read'

    # Only the first Filesystem needs an env; the others won't need to run processing, since they
    # are building from processed files.
    env = {}

    s3 = S3Bucket(m.s3_url, acl=acl, profile=m.args.profile)

    urls = []

    if (m.args.excel is not False or m.args.zip is not False or
            (hasattr(m.args, 'filesystem') and m.args.filesystem is not False)):
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    if m.args.force: # or distupdated is True:
        skip_if_exists = False
    else:
        skip_if_exists = True

    try:

        # Always create a filesystem package before ZIP or Excel, so we can use it as a source for
        # data for the other packages. This means that Transform processes and programs only need
        # to be run once.

        _, third_stage_mtfile, created = make_filesystem_package(second_stage_mtfile,  m.package_root, m.cache, get_lib_module_dict(doc), skip_if_exists)

        if m.args.excel is not False:
            _, ex_url, created = make_excel_package(third_stage_mtfile, m.package_root, m.cache, env, skip_if_exists)
            with open(ex_url.path, mode='rb') as f:
                urls.append(('excel', s3.write(f.read(), basename(ex_url.path), acl)))

        if m.args.zip is not False:
            _, zip_url, created = make_zip_package(third_stage_mtfile, m.package_root, m.cache, env, skip_if_exists)
            with open(zip_url.path, mode='rb') as f:
                urls.append(('zip', s3.write(f.read(), basename(zip_url.path), acl)))

        # Note! This is a FileSystem package on the remote S3 bucket, not locally
        if m.args.fs is not False:
            try:
                s3_package_root = MetapackPackageUrl(str(m.s3_url), downloader=third_stage_mtfile.downloader)
                fs_p, fs_url, created = make_s3_package(third_stage_mtfile, s3_package_root, m.cache, env, acl, skip_if_exists)
            except NoCredentialsError:
                print(getenv('AWS_SECRET_ACCESS_KEY'))
                err("Failed to find boto credentials for S3. "
                    "See http://boto3.readthedocs.io/en/latest/guide/configuration.html ")

            # A crappy hack. make_s3_package should return the correct url
            if access_value == 'private':
                urls.append(('fs', fs_p.private_access_url.inner))
            else:
                urls.append(('fs', fs_p.public_access_url.inner))

        # Make the CSV package from the filesystem package on S3; this will ensure that the
        # package's resource URLs point to the S3 objects
        if m.args.csv is not False:

            # Using the signed url in case the bucket is private

            u = MetapackUrl(fs_p.access_url, downloader=m.downloader)

            resource_root = u.dirname().as_type(MetapackPackageUrl)

            p = CsvPackageBuilder(u, m.package_root, resource_root)

            csv_url = p.save()

            with open(csv_url.path, mode='rb') as f:
                urls.append(('csv', s3.write(f.read(), csv_url.target_file, acl)))

    except PackageError as e:
        err("Failed to generate package: {}".format(e))



    return urls
