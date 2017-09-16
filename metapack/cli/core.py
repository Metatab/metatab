import logging
import sys
from genericpath import exists
from itertools import islice
from os.path import join
from uuid import uuid4

import six
from tableintuit import TypeIntuiter

from metapack import MetapackDoc, MetapackUrl
from metapack.package.s3 import S3PackageBuilder
from metapack.package.csv import CsvPackageBuilder
from metapack.package.excel import ExcelPackageBuilder
from metapack.package.filesystem import FileSystemPackageBuilder
from metapack.package.zip import ZipPackageBuilder
from metatab import  DEFAULT_METATAB_FILE
from metatab import _meta
from metatab.util import make_metatab_file
from rowgenerators import SelectiveRowGenerator
from appurl import parse_app_url
from os.path import dirname
from os import getenv

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
    logger.info(' '.join(str(e) for e in args),**kwargs)

def warn(*args, **kwargs):
    logger_err.warn(' '.join(str(e) for e in args),**kwargs)

def err(*args, **kwargs):
    logger_err.critical(' '.join(str(e) for e in args),**kwargs)
    sys.exit(1)



def datetime_now():
    import datetime

    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()


def metatab_info(cache):
    from tabulate import tabulate
    from rowgenerators._meta import __version__ as rg_ver
    from rowpipe._meta import __version__ as rp_ver

    table = [
        ('Version',_meta.__version__),
        ('Row Generators', rg_ver),
        ('Row Pipes', rp_ver),
        ('Cache Dir', str(cache.getsyspath('/'))),
    ]

    prt(tabulate(table))


def new_metatab_file(mt_file, template):
    template = template if template else 'metatab'

    if not exists(mt_file):
        doc = make_metatab_file(template)

        doc['Root']['Identifier'] = str(uuid4())

        doc.write_csv(mt_file)


def find_files(base_path, types):
    from os import walk
    from os.path import join, splitext

    for root, dirs, files in walk(base_path):
        if '_metapack' in root:
            continue

        for f in files:
            if f.startswith('_'):
                continue

            b, ext = splitext(f)
            if ext[1:] in types:
                yield join(root, f)


def get_lib_module_dict(doc):
    return doc.get_lib_module_dict()


def dump_resources(doc):
    for r in doc.resources():
        prt(r.name, r.resolved_url)


def dump_resource(doc, name, lines=None):
    import unicodecsv as csv
    import sys
    from itertools import islice
    from tabulate import tabulate
    from rowpipe.exceptions import CasterExceptionError, TooManyCastingErrors

    r = doc.resource(name=name)

    if not r:
        err("Did not get resource for name '{}'".format(name))

    # WARNING! This code will not generate errors if line is set ( as for the -H
    # option because the errors are tansfered from the row pipe to the resource after the
    # iterator is exhausted

    gen = islice(r, 1, lines)

    def dump_errors(error_set):
        for col, errors in error_set.items():
            warn("Errors in casting column '{}' in resource '{}' ".format(col, r.name))
            for error in errors:
                warn("    ", error)


    try:
        if lines and lines <= 20:
            try:
                prt(tabulate(list(gen), list(r.headers)))
            except TooManyCastingErrors as e:
                dump_errors(e.errors)
                err(e)

        else:

            w = csv.writer(sys.stdout if six.PY2 else sys.stdout.buffer)

            if r.headers:
                w.writerow(r.headers)
            else:
                warn("No headers for resource '{}'; have schemas been generated? ".format(name))

            for row in gen:
                w.writerow(row)

    except CasterExceptionError as e:  # Really bad errors, not just casting problems.
        raise e
        err(e)
    except TooManyCastingErrors as e:
        dump_errors(e.errors)
        err(e)

    dump_errors(r.errors)



def dump_schema(doc, name):
    from tabulate import tabulate

    t = get_table(doc, name)

    rows = []
    header = 'name altname datatype description'.split()
    for c in t.children:
        cp = c.properties
        rows.append([cp.get(h) for h in header])

    prt(tabulate(rows, header))


def get_table(doc, name):
    t = doc.find_first('Root.Table', value=name)

    if not t:

        table_names = ["'" + t.value + "'" for t in doc.find('Root.Table')]

        if not table_names:
            table_names = ["<No Tables>"]

        err("Did not find schema for table name '{}' Tables are: {}"
            .format(name, " ".join(table_names)))

    return t

PACKAGE_PREFIX = '_packages'

def make_excel_package(file, package_root, cache, env, skip_if_exists):

    assert package_root

    p = ExcelPackageBuilder(file, package_root, callback=prt,  env=env)
    prt('Making Excel Package')

    if not p.exists() or not skip_if_exists:
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():
        prt("Excel Package already exists")
        created = False
        url = p.package_path.path

    return p, MetapackUrl(url, downloader=package_root.downloader), created


def make_zip_package(file, package_root, cache, env, skip_if_exists):

    assert package_root


    p = ZipPackageBuilder(file, package_root, callback=prt,  env=env)
    prt('Making ZIP Package')
    if not p.exists() or not skip_if_exists:
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():
        prt("ZIP Package already exists")
        created = False
        url = p.package_path.path

    return p, MetapackUrl(url, downloader=package_root.downloader), created


def make_filesystem_package(file, package_root, cache, env, skip_if_exists):

    assert package_root

    p = FileSystemPackageBuilder(file, package_root, callback=prt, env=env)

    if skip_if_exists is None:
        skip_if_exists = p.is_older_than_metatada()

    if not p.exists() or not skip_if_exists:
        prt('Making Filesystem Package ',
            '; existing package is older than metadata {}'.format(file) if (p.exists() and not skip_if_exists) else '')
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():

        prt("Filesystem Package already exists")
        created = False
        url = join(p.package_path.path.rstrip('/'), DEFAULT_METATAB_FILE)

    return p, MetapackUrl(url, downloader=package_root.downloader), created


def make_csv_package(file, package_root, cache, env, skip_if_exists):
    assert package_root

    p = CsvPackageBuilder(file, package_root, callback=prt,  env=env)
    prt('Making CSV Package')
    if not p.exists() or not skip_if_exists:
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():
        prt("CSV Package already exists")
        created = False
        url = p.package_path.path

    return p, MetapackUrl(url, downloader=package_root.downloader), created

def make_s3_package(file, package_root,  cache,  env,  skip_if_exists, acl='public-read'):

    assert package_root

    p = S3PackageBuilder(file, package_root, callback=prt,  env=env, acl=acl)

    prt('Making S3 Package')
    if not p.exists() or not skip_if_exists:
        url = p.save()
        prt("Packaged saved to: {}".format(url))
        created = True
    elif p.exists():
        prt("S3 Package already exists")
        created = False
        url = p.access_url

    return p, MetapackUrl(url, downloader=file.downloader), created


def update_name(mt_file, fail_on_missing=False, report_unchanged=True, force=False):

    if isinstance(mt_file, MetapackDoc):
        doc = mt_file
    else:
        doc = MetapackDoc(mt_file)

    o_name = doc.find_first_value("Root.Name", section=['Identity', 'Root'])

    updates = doc.update_name(force=force)

    for u in updates:
        prt(u)

    prt("Name is: ", doc.find_first_value("Root.Name", section=['Identity', 'Root']))

    if o_name != doc.find_first_value("Root.Name", section=['Identity', 'Root']) or force:
        write_doc(doc, mt_file)


def write_doc(doc, mt_file):
    """
    Write a Metatab doc to a CSV file, and update the Modified time
    :param doc:
    :param mt_file:
    :return:
    """

    t = doc['Root'].get_or_new_term('Root.Modified')
    t.value = datetime_now()

    doc['Root'].sort_by_term(order = [
        'Root.Declare',
        'Root.Title',
        'Root.Description',
        'Root.Identifier',
        'Root.Name',
        'Root.Dataset',
        'Root.Origin',
        'Root.Time',
        'Root.Space',
        'Root.Grain',
        'Root.Version',
        'Root.Group',
        'Root.Tag',
        'Root.Keyword',
        'Root.Subject',
        'Root.Created',
        'Root.Modified',
        'Root.Issued',
        'Root.Access',
        'Root.Access',
        'Root.Distribution'
    ])

    import subprocess

    try:
        out = subprocess.run(['git', 'remote', 'show','origin'], stdout=subprocess.PIPE, timeout=6)\
            .stdout.decode('utf-8')

        fetchline = next(l.split() for l in out.splitlines() if 'Fetch' in l )
    except (TimeoutError, StopIteration, subprocess.TimeoutExpired):
        fetchline = None

    if fetchline:
        t = doc['Root'].get_or_new_term('GitUrl')
        t.value = fetchline[-1]

    u = parse_app_url(mt_file)

    if u.scheme == 'file':
        doc.write_csv(mt_file)
        return True
    else:
        return False
        #warn("Not writing back to url ", mt_file)


def process_schemas(mt_file, cache=None, clean=False):
    from rowgenerators import SourceError
    from requests.exceptions import ConnectionError

    if isinstance(mt_file, MetapackDoc):
        doc = mt_file
        write_doc_to_file = False
    else:
        doc = MetapackDoc(mt_file)
        write_doc_to_file = True

    try:
        if clean:
            doc['Schema'].clean()
        else:
            doc['Schema']

    except KeyError:
        doc.new_section('Schema', ['DataType', 'Altname', 'Description'])

    for r in doc['Resources'].find('Root.Resource'):

        schema_term = r.schema_term

        if schema_term:
            prt("Found table for '{}'; skipping".format(r.schema_name))
            continue

        path, name = extract_path_name(r.url)

        prt("Processing {}".format(r.url))

        slice = islice(r.row_generator, 100)

        si = SelectiveRowGenerator(slice,
                                   headers=[int(i) for i in r.get_value('headerlines', '0').split(',')],
                                   start=int(r.get_value('startline', 1)))

        try:
            ti = TypeIntuiter().run(si)
        except SourceError as e:
            warn("Failed to process '{}'; {}".format(path, e))
            continue
        except ConnectionError as e:
            warn("Failed to download '{}'; {}".format(path, e))
            continue

        table = doc['Schema'].new_term('Table', r.schema_name)

        prt("Adding table '{}' ".format(r.schema_name))

        for i, c in enumerate(ti.to_rows()):

            raw_alt_name = alt_col_name(c['header'], i)
            alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

            t = table.new_child('Column', c['header'],
                            datatype=type_map.get(c['resolved_type'], c['resolved_type']),
                            altname=alt_name)

    if write_doc_to_file:
        write_doc(doc, mt_file)


def extract_path_name(ref):
    from os.path import splitext, basename, abspath

    uparts = parse_app_url(ref)

    ss = parse_app_url(ref)

    if not uparts.scheme:
        path = abspath(ref)
        name = basename(splitext(path)[0])
    else:
        path = ref

        v = ss.target_file if ss.target_file else uparts.path

        name = basename(splitext(v)[0])

    return path, name


def alt_col_name(name, i):
    import re

    if not name:
        return 'col{}'.format(i)

    return re.sub('_+', '_', re.sub('[^\w_]', '_', str(name)).lower()).rstrip('_')


type_map = {
    float.__name__: 'number',
    int.__name__: 'integer',
    six.text_type.__name__: 'string',
    six.binary_type.__name__: 'text',

}


class MetapackCliMemo(object):
    def __init__(self, args, downloader):
        from os import getcwd

        self.cwd = getcwd()
        self.args = args

        self.downloader = downloader

        self.cache = self.downloader.cache

        frag = ''

        # Just the fragment was provided
        if args.metatabfile and args.metatabfile.startswith('#'):
            frag = args.metatabfile
            mtf = None
        else:
            frag = ''
            mtf = args.metatabfile

        # If could not get it from the args, Set it to the default file name in the current dir
        if not mtf:
            mtf = join(self.cwd, DEFAULT_METATAB_FILE)

        self.init_stage2(mtf, frag)



    def init_stage2(self, mtf, frag):

        self.frag = frag
        self.mtfile_arg = mtf + frag

        self.mtfile_url = MetapackUrl(self.mtfile_arg, downloader=self.downloader)

        self.resource = self.mtfile_url.fragment

        self.package_url = self.mtfile_url.package_url
        self.mt_file = self.mtfile_url.metadata_url

        assert self.package_url.scheme == 'file'
        self.package_root = self.package_url.join(PACKAGE_PREFIX)
        assert self.package_root._downloader


def update_dist(doc, old_dists, v):

    # This isn't quite correct, because it will try to remove the .csv format
    # Distributions twice, since both <name>.csv and <name>/metadata.csv have the same format.
    # (That's why theres a try/except ) But, it is effective

    name = doc.find_first_value("Root.Name")

    for d in old_dists:

        if parse_app_url(d.value).resource_format == parse_app_url(v).resource_format and name not in d.value:
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