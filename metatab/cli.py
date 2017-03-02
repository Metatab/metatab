# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

from __future__ import print_function

import json
import sys
import collections
from itertools import islice
from uuid import uuid4
import re

import six
from metatab.util import make_metatab_file, slugify
from metatab import _meta, MetatabError, ConversionError
from metatab.doc import MetatabDoc, resolve_package_metadata_url, DEFAULT_METATAB_FILE
from os import getcwd
from os.path import exists, join, isdir, abspath, dirname
from rowgenerators import RowGenerator, Url, SourceError
from tableintuit import TypeIntuiter, SelectiveRowGenerator, RowIntuitError

DATA_FORMATS = ('xls', 'xlsx', 'tsv', 'csv')
DOC_FORMATS = ('pdf', 'doc', 'docx', 'html')

# Change the row cache name
from rowgenerators.util import get_cache, clean_cache

def prt(*args, **kwargs):
    print(*args, **kwargs)


def warn(*args, **kwargs):
    print('WARN:', *args, file=sys.stderr, **kwargs)


def err(*args, **kwargs):
    import sys
    print("ERROR:", *args, file=sys.stderr, **kwargs)
    sys.exit(1)


def load_plugins(parser):

    import metatab_plugins._plugins as mtp

    for p in mtp.metatab_plugins_list:
        p(parser)


def metatab():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metatab',
        description='Matatab file parser, version {}'.format(_meta.__version__))

    parser.add_argument('-C', '--clean-cache', default=False, action='store_true',
                        help="Clean the download cache")

    g = parser.add_mutually_exclusive_group(required=True)

    g.add_argument('-i', '--info', default=False, action='store_true',
                        help="Show configuration information")

    g.add_argument('-c', '--create', action='store', nargs='?', default=False,
                   help="Create a new metatab file, from named template. With no argument, uses the 'metatab' template ")

    g.add_argument('-t', '--terms', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, before interpretation')

    g.add_argument('-I', '--interp', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, after interpretation')

    g.add_argument('-j', '--json', default=False, action='store_true',
                   help='Parse a file and print out a JSON representation')

    g.add_argument('-y', '--yaml', default=False, action='store_true',
                   help='Parse a file and print out a YAML representation')

    g.add_argument('-R', '--resource', default=False, action='store_true',
                   help='If the URL has no fragment, dump the resources listed in the metatab file. With a fragment, dump a resource as a CSV')

    g.add_argument('-H', '--head', default=False, action='store_true',
                   help="Dump the first 20 lines of a resoruce ")

    g.add_argument('-S', '--schema',
                   help='Dump the schema for one named resource')

    parser.add_argument('-d', '--show-declaration', default=False, action='store_true',
                        help='Parse a declaration file and print out declaration dict. Use -j or -y for the format')

    parser.add_argument('-D', '--declare', help='Parse and incorporate a declaration before parsing the file.' +
                                                ' (Adds the declaration to the start of the file as the first term. )')



    parser.add_argument('file', nargs='?', default=DEFAULT_METATAB_FILE, help='Path to a Metatab file')

    args = parser.parse_args(sys.argv[1:])

    # Specing a fragment screws up setting the default metadata file name
    if args.file.startswith('#'):
        args.file = DEFAULT_METATAB_FILE + args.file

    cache = get_cache('metapack')

    if args.info:
        prt('Version  : {}'.format(_meta.__version__))
        prt('Cache dir: {}'.format(str(cache.getsyspath('/'))))
        exit(0)

    if args.clean_cache:
        clean_cache('metapack')

    if args.create is not False:
        new_metatab_file(args.file, args.create)
        exit(0)

    if args.resource or args.head:

        limit = 20 if args.head else None

        u = Url(args.file)
        resource = u.parts.fragment
        metadata_url = u.rebuild_url(False,False)

        package_url, metadata_url = resolve_package_metadata_url(metadata_url)

        try:
            doc = MetatabDoc(metadata_url, cache=cache)
        except OSError as e:

            err("Failed to open Metatab doc: {}".format(e))

        if resource:
            dump_resource(doc, resource, limit)
        else:
            dump_resources(doc)

        exit(0)

    if args.show_declaration:

        doc = MetatabDoc()
        doc.load_declarations([args.file])

        print(json.dumps({
            'terms': doc.decl_terms,
            'sections': doc.decl_sections
        }, indent=4))
        exit(0)
    else:

        package_url, metadata_url = resolve_package_metadata_url(args.file)
        try:
            doc = MetatabDoc(metadata_url, cache=cache)
        except IOError as e:
            err("Failed to open '{}': {}".format(metadata_url,e))

    if args.terms:
        for t in doc._term_parser:
            print(t)

    elif args.json:
        print(json.dumps(doc.as_dict(), indent=4))


    elif args.yaml:
        import yaml
        print(yaml.safe_dump(doc.as_dict(), default_flow_style=False, indent=4))


    elif args.schema:
        dump_schema(doc, args.schema)

    exit(0)


def metatab_info(cache):

    prt('Version  : {}'.format(_meta.__version__))
    prt('Cache dir: {}'.format(str(cache.getsyspath('/'))))

    print(__file__)

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


def dump_resources(doc):
    for r in doc.resources():
        print(r.name, r.resolved_url)

def get_lib_module_dict(doc):

    from os.path import dirname, abspath
    from importlib import import_module
    import sys

    u = Url(doc.ref)
    if u.proto == 'file':

        # Add the dir with the metatab file to the system path
        sys.path.append(dirname(abspath(u.parts.path)))

        try:
            m = import_module("lib")
            return { k:v for k,v in m.__dict__.items() if k in m.__all__ }
        except ImportError:
            return {}

    else:
        return {}

def dump_resource(doc, name, lines=None):
    import unicodecsv as csv
    import sys
    from itertools import islice
    from tabulate import tabulate
    from rowpipe.exceptions import CasterExceptionError

    r = doc.resource(name=name, env=get_lib_module_dict(doc))

    # WARNING! This code will not generate errors if line is set ( as for the -H
    # option because the errors are tansfered from the row pipe to the resource after the
    # iterator is exhausted

    if lines:
        try:
            gen = islice(r, int(r.startline), lines)
        except ValueError:
            gen = islice(r, lines)
    else:
        gen = r

    if not r.headers():
        print(r.schema_table, r.name, r.schema)
        err("No headers for resource '{}'; have schemas been generated? ".format(name))

    try:
        if lines and lines <= 20:
            print(tabulate(list(gen),list(r.headers())))

        else:

            w = csv.writer(sys.stdout if six.PY2 else sys.stdout.buffer)

            w.writerow(r.headers())

            for row in gen:
                w.writerow(row)

    except CasterExceptionError as e: # Really bad errors, not just casting problems.
        err(e)

    for col, errors in r.errors.items():
        warn("Errors in casting column '{}' in resource '{}' ".format(col, r.name))
        for e in errors:
            warn("    ",e)

def get_table(doc, name):
    t = doc.find_first('Root.Table', value=name)

    if not t:

        table_names = ["'" + t.value + "'" for t in doc.find('Root.Table')]

        if not table_names:
            table_names = ["<No Tables>"]

        err("Did not find schema for table name '{}' Tables are: {}"
            .format(name, " ".join(table_names)))

    return t


def dump_schema(doc, name):
    from tabulate import tabulate

    t = get_table(doc, name)

    rows = []
    header = 'name altname datatype description'.split()
    for c in t.children:
        cp = c.properties
        rows.append([cp.get(h) for h in header])

    prt(tabulate(rows, header))


def metapack():
    import argparse

    parser = argparse.ArgumentParser(
        prog='metapack',
        description='Create and manipulate metatab data packages, version {}'.format(_meta.__version__))

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    parser.set_defaults(handler=None)

    ##
    ## Build Group

    build_group = parser.add_argument_group('Building Metatab Files', 'Build and manage a metatab file for a pacakge')

    build_group.add_argument('-c', '--create', action='store', nargs='?', default=False,
                        help="Create a new metatab file, from named template. With no argument, uses the "
                             "'metatab' template ")

    build_group.add_argument('-a', '--add', default=False,
                        help='Add a file or url to the resources. With a directory add a data files in the directory. '
                             'If given a URL to a web page, will add all links that point to CSV, Excel Files and'
                             'data files in ZIP files. (Caution: it will download and cache all of these files. )')

    #build_group.add_argument('-S', '--scrape',
    #                help='Similar to --add, but scrape a web page for links to data files, documentation '
    #                     'and web pages and add the links as resources ')

    #build_group.add_argument('-r', '--resources', default=False, action='store_true',
    #                    help='Rebuild the resources, intuiting rows and encodings from the URLs')


    build_group.add_argument('-s', '--schemas', default=False, action='store_true',
                        help='Rebuild the schemas for files referenced in the resource section')

    build_group.add_argument('-d', '--datapackage', action='store_true', default=False,
                        help="Write a datapackage.json file adjacent to the metatab file")

    build_group.add_argument('-u', '--update', action='store_true', default=False,
                        help="Update the Name from the Datasetname, Origin and Version terms")



    ##
    ## Derived Package Group

    derived_group = parser.add_argument_group('Derived Packages','Generate other types of packages')

    derived_group.add_argument('-e', '--excel', action='store_true', default=False,
                        help='Create an excel archive from a metatab file')

    derived_group.add_argument('-z', '--zip', action='store_true', default=False,
                        help='Create a zip archive from a metatab file')

    derived_group.add_argument('-f', '--filesystem', action='store_true', default=False,
                        help='Create a filesystem archive from a metatab file')

    derived_group.add_argument('-s3', '--s3', action='store',
                        help='Create a s3 archive from a metatab file. Argument is an S3 URL with the bucket name and '
                             'prefix, such as "s3://devel.metatab.org:/excel/". Uses boto configuration for credentials')

    ##
    ## QueryPackage Group

    query_group = parser.add_argument_group('Query', 'Return information and data from a package')

    query_group.add_argument('-r', '--resource', default=False, action='store_true',
                        help='If the URL has no fragment, dump the resources listed in the metatab file.'
                             ' With a fragment, dump a resource as a CSV')

    query_group.add_argument('-H', '--head', default=False, action='store_true',
                    help="Dump the first 20 lines of a resource ")


    ##
    ## Administration Group

    admin_group = parser.add_argument_group('Administration', 'Information and administration')

    admin_group.add_argument('--clean-cache', default=False, action='store_true',
                        help="Clean the download cache")

    admin_group.add_argument('-C', '--clean', default=False, action='store_true',
                        help="For some operations, like updating schemas, clear the section of existing terms first")

    admin_group.add_argument('-i', '--info', default=False, action='store_true',
                        help="Show configuration information")

    admin_group.add_argument('-E', '--enumerate',
                        help='Enumerate the resources referenced from a URL. Does not alter the Metatab file')

    #cmd = parser.add_subparsers(title='Plugin Commands', help='Additional command supplied by plugins')
    #load_plugins(cmd)

    class MetapackCliMemo(object):

        def __init__(self, args):
            self.cwd = getcwd()
            self.args = args
            self.cache = get_cache('metapack')

            self.mtfile_arg = args.metatabfile if args.metatabfile else join(self.cwd, DEFAULT_METATAB_FILE)

            self.mtfile_url = Url(self.mtfile_arg)
            self.resource = self.mtfile_url.parts.fragment

            self.package_url, self.mt_file = resolve_package_metadata_url(self.mtfile_url.rebuild_url(False, False))

    m = MetapackCliMemo(parser.parse_args(sys.argv[1:]))

    for handler in (metatab_build_handler, metatab_derived_handler, metatab_query_handler,  metatab_admin_handler):
        handler(m)

    clean_cache("metapack")

def metatab_build_handler(m):

    if m.args.create is not False:

        template =  m.args.create if  m.args.create else 'metatab'

        mt_file = Url(m.mt_file_url).parts.path

        if not exists(mt_file):
            doc = make_metatab_file(template)

            doc[('Identity', 'Root')]['Identifier'] = six.text_type(uuid4())

            doc.write_csv(mt_file)

            prt('Created', mt_file)
        else:
            err('File', mt_file, 'already exists')


    if m.args.add:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        add_resource(m.mt_file, m.args.add, cache=m.cache)

    if False: #m.args.resources:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        doc = MetatabDoc(m.mt_file)

        try:
            doc['Schema'].clean()
        except KeyError:
            pass

        for t in list(doc['Resources']):  # w/o list(), will iterate over new terms

            if not t.term_is('root.datafile'):
                continue

            if t.as_dict().get('url'):
                add_resource(doc, t.as_dict()['url'], m.cache)

            else:
                warn("Entry '{}' on row {} is missing a url; skipping".format(t.join, t.row))

        doc.write_csv(m.mt_file)


    if m.args.schemas:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        process_schemas(m.mt_file, cache=m.cache, clean=m.args.clean)


    if m.args.datapackage:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        from metatab.datapackage import convert_to_datapackage

        doc = MetatabDoc(m.mt_file)

        u = Url(m.mt_file)

        if u.proto == 'file':
            dpj_file = join(dirname(abspath(u.parts.path)), 'datapackage.json')
        else:
            dpj_file = join(getcwd(), 'datapackage.json')

        try:
            with open(dpj_file, 'w') as f:
                f.write(json.dumps(convert_to_datapackage(doc), indent=4))
        except ConversionError as e:
            err(e)

    if m.mtfile_url.scheme == 'file' and m.args.update:
        update_name(m.mt_file, fail_on_missing=True)

def metatab_derived_handler(m):
    from metatab.package import ZipPackage, ExcelPackage, FileSystemPackage , S3Package, PackageError

    try:

        if m.args.excel is not False:
            update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)
            p = ExcelPackage(m.mt_file, callback=prt, cache=m.cache)
            p.save()

        if m.args.zip is not False:
            update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)
            p = ZipPackage(m.mt_file, callback=prt, cache=m.cache)
            p.save()

        if m.args.filesystem is not False:
            update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)
            p = FileSystemPackage(m.mt_file, callback=prt, cache=m.cache)
            p.save()

        if m.args.s3:
            update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)
            p = S3Package(m.mt_file, callback=prt, cache=m.cache)
            p.save( m.args.s3)

    except PackageError as e:
        err("Failed to generate package: {}".format(e))



def metatab_query_handler(m):

    if m.args.resource or m.args.head:

        limit = 20 if m.args.head else None

        try:
            doc = MetatabDoc(m.mt_file, cache=m.cache)
        except OSError as e:
            err("Failed to open Metatab doc: {}".format(e))

        if m.resource:
            dump_resource(doc, m.resource, limit)
        else:
            dump_resources(doc)


def metatab_admin_handler(m):

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    if m.args.enumerate:

        from metatab.util import enumerate_contents

        specs = list(enumerate_contents(m.args.enumerate, m.cache, callback=prt))

        for s in specs:
            print(classify_url(s.url), s.target_format, s.url, s.target_segment)

    if m.args.clean_cache:
        clean_cache('metapack')




def find_files(base_path, types):
    from os import walk
    from os.path import join, splitext
    from rowgenerators import Url

    for root, dirs, files in walk(base_path):
        if '_metapack' in root:
            continue

        for f in files:
            if f.startswith('_'):
                continue

            u = Url(f)

            if u.target_format in types:
                yield join(root, f)


def init_metatab(mt_file, alt_mt_file):
    mt_file = alt_mt_file if alt_mt_file else mt_file

    prt("Initializing '{}'".format(mt_file))

    if not exists(mt_file):
        doc = make_metatab_file()

        doc['Root']['Identifier'] = str(uuid4())

        doc.write_csv(mt_file)
    else:
        prt("Doing nothing; file '{}' already exists".format(mt_file))


def classify_url(url):
    from rowgenerators import SourceSpec

    ss = SourceSpec(url=url)

    if ss.target_format in DATA_FORMATS:
        term_name = 'DataFile'
    elif ss.target_format in DOC_FORMATS:
        term_name = 'Documentation'
    else:
        term_name = 'Resource'

    return term_name





def run_row_intuit(path, cache):
    from rowgenerators import RowGenerator
    from tableintuit import RowIntuiter
    from itertools import islice
    from rowgenerators import TextEncodingError

    for encoding in ('ascii',  'utf8', 'latin1'):
        try:
            rows = list(islice(RowGenerator(url=path, encoding=encoding, cache=cache), 5000))
            return encoding, RowIntuiter().run(list(rows))
        except (TextEncodingError, UnicodeEncodeError) as e:
            pass

    raise RowIntuitError('Failed to convert with any encoding')



def scrape_page(mt_file, url):
    from .util import scrape_urls_from_web_page

    doc = MetatabDoc(mt_file)

    doc['resources'].new_term('DownloadPage', url)

    d = scrape_urls_from_web_page(url)

    for k, v in d['sources'].items():
        doc['Resources'].new_term('DataFile', v['url'], description=v.get('description'))

    for k, v in d['external_documentation'].items():
        term_name = classify_url(v['url'])
        doc['Documentation'].new_term(term_name, v['url'], description=v.get('description'))

    doc.write_csv(mt_file)



def add_resource(mt_file, ref, cache):
    """Add a resources entry, downloading the intuiting the file, replacing entries with
    the same reference"""
    from metatab.util import enumerate_contents
    from rowgenerators import Url

    if isinstance(mt_file, MetatabDoc):
        doc = mt_file
    else:
        doc = MetatabDoc(mt_file)

    seen_names = set()

    if isdir(ref):
        for f in find_files(ref, DATA_FORMATS):

            if f.endswith(DEFAULT_METATAB_FILE):
                continue

            if doc.find_first('Root.Datafile', value=f):
                prt("Datafile exists for '{}', ignoring".format(f))
            else:
                add_single_resource(doc, f, cache=cache, seen_names=seen_names)
    else:

        for c in enumerate_contents(ref, cache=cache, callback=prt):
            add_single_resource(doc, c.rebuild_url(), cache=cache, seen_names=seen_names)

    doc.write_csv(mt_file)


def add_single_resource(doc, ref, cache, seen_names):
    from metatab.util import slugify

    t = doc.find_first('Root.Datafile', value=ref)

    if t:
        prt("Datafile exists for '{}', deleting".format(ref))
        doc.remove_term(t)

    term_name = classify_url(ref)

    path, name = extract_path_name(ref)

    if name in seen_names:
        base_name = re.sub(r'-?\d+$', '', name)

        for i in range(1, 20):
            name = "{}-{}".format(base_name, i)
            if name not in seen_names:
                break

    seen_names.add(name)

    encoding = start_line  = None
    header_lines = []

    try:
        encoding, ri = run_row_intuit(path, cache)
        prt("Added resource for '{}', name = '{}' ".format(ref, name))
        start_line = ri.start_line
        header_lines = ri.header_lines
    except RowIntuitError as e:
        warn("Failed to intuit '{}'; {}".format(path, e))

    except SourceError as e:
        warn("Source Error: '{}'; {}".format(path, e))


    if not name:
        from hashlib import sha1
        name = sha1(slugify(path).encode('ascii')).hexdigest()[:12]

        # xlrd gets grouchy if the name doesn't start with a char
        try:
            int(name[0])
            name = 'a' + name[1:]
        except:
            pass

    return doc['Resources'].new_term(term_name, ref, name=name,
                                     startline=start_line,
                                     headerlines=','.join(str(e) for e in header_lines),
                                     encoding=encoding)

def extract_path_name(ref):
    from os.path import splitext, basename, abspath
    from rowgenerators.util import parse_url_to_dict
    from rowgenerators import SourceSpec

    uparts = parse_url_to_dict(ref)

    ss = SourceSpec(url=ref)

    if not uparts['scheme']:
        path = abspath(ref)
        name = basename(splitext(path)[0])
    else:
        path = ref

        v = ss.target_file if ss.target_file else uparts['path']

        name = basename(splitext(v)[0])

    return path, name


def alt_col_name(name, i):
    import re
    if not name:
        return 'col{}'.format(i)
    return re.sub('_+', '_', re.sub('[^\w_]', '_', name).lower()).rstrip('_')



type_map = {
    float.__name__: 'number',
    int.__name__: 'integer',
    six.text_type.__name__: 'string',
    six.binary_type.__name__: 'text',

}


def process_schemas(mt_file, cache, clean=False):
    from rowgenerators import SourceError
    from requests.exceptions import ConnectionError

    doc = MetatabDoc(mt_file)

    try:
        if clean:
            doc['Schema'].clean()
        else:
            doc['Schema']
    except KeyError:
        doc.new_section('Schema', ['DataType', 'Altname', 'Description'])

    for t in doc['Resources']:

        if not t.term_is('root.datafile'):
            continue

        e = {k: v for k, v in t.properties.items() if v}

        schema_term = doc.find_first(term='Table', value=e['name'], section='Schema')

        if schema_term:
            prt("Found table for '{}'; skipping".format(e['name']))
            continue

        path, name = extract_path_name(t.value)

        prt("Processing {}".format(t.value))

        rg = RowGenerator(url=path,
                          name=e.get('name'),
                          encoding=e.get('encoding', 'utf8'),
                          target_format=e.get('format'),
                          target_file=e.get('file'),
                          target_segment=e.get('segment'),
                          cache=cache)

        si = SelectiveRowGenerator(islice(rg, 5000),
                                   headers=[int(i) for i in e.get('headerlines', '0').split(',')],
                                   start=int(e.get('startline', 1)))

        try:
            ti = TypeIntuiter().run(si)
        except SourceError as e:
            warn("Failed to process '{}'; {}".format(path, e))
            continue
        except ConnectionError as e:
            warn("Failed to download '{}'; {}".format(path, e))
            continue

        table = doc['Schema'].new_term('Table', e['name'])

        prt("Adding table '{}' ".format(e['name']))

        for i, c in enumerate(ti.to_rows()):
            raw_alt_name = alt_col_name(c['header'], i)
            alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

            table.new_child('Column', c['header'],
                            datatype=type_map.get(c['resolved_type'], c['resolved_type']),
                            altname=alt_name)

    doc.write_csv(mt_file)

def rewrite_resource_format(mt_file):
    doc = MetatabDoc(mt_file)

    if 'schema' in doc:
        table_schemas = {t.value: t.as_dict() for t in doc['schema']}
        del doc['schema']

        for resource in doc['resources']:
            s = resource.new_child('Schema', '')
            for column in table_schemas.get(resource.find_value('name'), {})['column']:
                c = s.new_child('column', column['name'])

                for k, v in column.items():
                    if k != 'name':
                        c.new_child(k, v)

    doc.write_csv(mt_file)


def update_name(mt_file, fail_on_missing=False, report_unchanged = True):

    if isinstance(mt_file, MetatabDoc):
        doc = mt_file
    else:
        doc = MetatabDoc(mt_file)

    updates = doc.update_name()

    for u in updates:
        prt(u)

    prt("Name is: ", doc.find_first_value("Root.Name", section=['Identity','Root']))

    doc.write_csv(mt_file)



