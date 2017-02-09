# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

from __future__ import print_function

import json
import sys
from itertools import islice
from uuid import uuid4

import six
from metatab.util import make_metatab_file
from metatab import _meta
from metatab.doc import MetatabDoc
from os import getcwd
from os.path import exists, join, isdir
from rowgenerators import RowGenerator
from tableintuit import TypeIntuiter, SelectiveRowGenerator

METATAB_FILE = 'metadata.csv'

# Change the row cache name
from rowgenerators.util import get_cache, clean_cache

LE = 'metadata.csv'

def prt(*args):
    print(*args)

def warn(*args):
    print('WARN:', *args)

def err(*args):
    import sys
    print("ERROR:", *args)
    sys.exit(1)


def metatab():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metatab',
        description='Simple Structured Table format parser, version {}'.format(_meta.__version__))

    parser.add_argument('-C', '--clean-cache', default=False, action='store_true',
                        help="Clean the download cache")

    g = parser.add_mutually_exclusive_group(required=True)

    g.add_argument('-c', '--create',  action='store', nargs='?', default=False,
                   help="Create a new metatab file, from named template. With no argument, uses the 'metatab' template ")

    g.add_argument('-t', '--terms', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, before interpretation')
    g.add_argument('-i', '--interp', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, after interpretation')

    g.add_argument('-j', '--json', default=False, action='store_true',
                   help='Parse a file and print out a JSON representation')
    g.add_argument('-y', '--yaml', default=False, action='store_true',
                   help='Parse a file and print out a YAML representation')

    g.add_argument('-r', '--resources', default=False, action='store_true',
                   help='Print the term name, resource name and url for all resources')

    g.add_argument('-R', '--resource',
                   help='Dump CSV for one named resource')

    parser.add_argument('-d', '--show-declaration', default=False, action='store_true',
                        help='Parse a declaration file and print out declaration dict. Use -j or -y for the format')

    parser.add_argument('-D', '--declare', help='Parse and incorporate a declaration before parsing the file.' +
                                                ' (Adds the declaration to the start of the file as the first term. )')

    g.add_argument('-V', '--version', default=False, action='store_true',
                   help='Display the package version and exit')

    parser.add_argument('file', help='Path to a Metatab file')

    args = parser.parse_args(sys.argv[1:])

    cache = get_cache('metapack')

    if args.clean_cache:
        clean_cache('metapack')

    if args.create:
        new_metatab_file(args.file, args.create)
        exit(0)

    if args.declare:
        raise NotImplementedError()

    elif args.package:
        raise NotImplementedError


    if args.show_declaration:

        doc = MetatabDoc()
        doc.load_declarations([args.file])

        print(json.dumps({
            'terms': doc.decl_terms,
            'sections': doc.decl_sections
        }, indent=4))
        exit(0)
    else:
        doc = MetatabDoc(args.file, cache=cache)

    if args.terms:
        for t in doc._term_parser:
            print(t)

    elif args.json:
        print(json.dumps(doc.as_dict(), indent=4))


    elif args.yaml:
        import yaml
        print(yaml.safe_dump(doc.as_dict(), default_flow_style=False, indent=4))

    elif args.resources:
        dump_resources(doc)

    elif args.resource:
        dump_resource(doc, args.resource)

    exit(0)


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

def dump_resource(doc, name):
    import unicodecsv as csv
    import sys

    r = list(doc.resources(name=name))[0]

    prt("Dumping resource at "+r._resolved_url())

    w = csv.writer(sys.stdout.buffer)

    for row in r:
        w.writerow(row)


def metapack():
    import argparse

    parser = argparse.ArgumentParser(
        prog='metapack',
        description='Create metatab data packages, version {}'.format(_meta.__version__))

    parser.add_argument('-C', '--clean-cache', default=False, action='store_true',
                   help="Clean the download cache")

    parser.add_argument('-i', '--init', action='store', nargs='?', default=False,
                        help='Set the cache directory for downloads and building packages')

    parser.add_argument('-a', '--add', default=False,
                        help='Add a file or url to the resources. With a directory add a data files in the directory')

    parser.add_argument('-S', '--scrape',
                        help='Scrape a web page for links to data files, documentation and web pages. ')

    parser.add_argument('-E', '--enumerate',
                        help='Enumerate the resources referenced from a URL')

    parser.add_argument('-r', '--resources', default=False, action='store_true',
                        help='Rebuild the resources, intuiting rows and encodings from the URLs')

    parser.add_argument('-s', '--schemas', default=False, action='store_true',
                        help='Rebuild the schemas for files referenced in the resource section')

    parser.add_argument('-e', '--excel', action='store_true', default=False,
                        help='Create an excel archive from a metatab file')

    parser.add_argument('-z', '--zip', action='store_true', default=False,
                        help='Create a zip archive from a metatab file')

    parser.add_argument('-f', '--filesystem', action='store_true', default=False,
                        help='Create a filesystem archive from a metatab file')

    parser.add_argument('-s3', '--s3', action='store',
                        help='Create a s3 archive from a metatab file')

    parser.add_argument('-R', '--resource-format', action='store_true', default=False,
                        help="Re-write the metatab file in 'Resource' format ")

    parser.add_argument('metatabfile', nargs='?')

    args = parser.parse_args(sys.argv[1:])

    d = getcwd()

    if args.clean_cache:
        clean_cache('metapack')

    cache = get_cache('metapack')

    prt('Cache dir: {}'.format(str(cache.getsyspath('/'))))

    mt_file = args.metatabfile if args.metatabfile else join(d, METATAB_FILE)

    if args.init is not False:
        init_metatab(mt_file, args.init)

    if args.scrape:
        scrape_page(mt_file, args.scrape)

    if args.enumerate:
        enumerate_contents( args.enumerate, cache=cache)

    if args.resources:
        process_resources(mt_file, cache=cache)

    if args.schemas:
        process_schemas(mt_file, cache=cache)

    if args.add:
        add_resource(mt_file, args.add, cache=cache)

    if args.excel is not False:
        write_excel_package(mt_file, args.excel, cache=cache)

    if args.zip is not False:
        write_zip_package(mt_file, args.zip, cache=cache)

    if args.filesystem is not False:
        write_dir_package(mt_file, args.filesystem, cache=cache)

    if args.s3:
        write_s3_package(mt_file, args.s3, cache=cache)

    if args.resource_format:
        rewrite_resource_format(mt_file)

    clean_cache("metapack")


def new_metatab_file(mt_file, template):
    template = template if template else 'metatab'

    if not exists(mt_file):
        doc = make_metatab_file(template)

        doc['Root']['Identifier'] = six.text_type(uuid4())

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

    if ss.target_format in ('xls', 'xlsx', 'tsv', 'csv'):
        term_name = 'DataFile'
    elif ss.target_format in ('pdf', 'doc', 'docx', 'html'):
        term_name = 'Documentation'
    else:
        term_name = 'Resource'

    return term_name


def add_single_resource(doc, ref, cache):
    from metatab.util import slugify

    t = doc.find_first('Root.Datafile', value=ref)

    if t:
        prt("Datafile exists for '{}', deleting".format(ref))
        doc.remove_term(t)

    term_name = classify_url(ref)

    path, name = extract_path_name(ref)

    prt("Adding resource for '{}'".format(ref))
    try:
        encoding, ri = run_row_intuit(path, cache)
    except Exception as e:
        warn("Failed to intuit '{}'; {}".format(path, e))
        return None

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
                                     startline=ri.start_line,
                                     headerlines=','.join(str(e) for e in ri.header_lines),
                                     encoding=encoding)


def scrape_page(mt_file, url):
    from .util import scrape_urls_from_web_page

    doc = MetatabDoc().load_csv(mt_file)

    doc['resources'].new_term('DownloadPage', url)

    d = scrape_urls_from_web_page(url)

    for k, v in d['sources'].items():
        doc['Resources'].new_term('DataFile', v['url'], description=v.get('description'))

    for k, v in d['external_documentation'].items():
        term_name = classify_url(v['url'])
        doc['Documentation'].new_term(term_name, v['url'], description=v.get('description'))

    doc.write_csv(mt_file)

def enumerate_contents(url, cache):

    from metatab.util import enumerate_contents

    specs = list(enumerate_contents(url, cache, callback=prt))

    for s in specs:
        print (classify_url(s.url), s.target_format, s.url, s.target_segment)

def add_resource(mt_file, ref, cache):
    """Add a resources entry, downloading the intuiting the file, replacing entries with
    the same reference"""
    from metatab.util import enumerate_contents

    doc = MetatabDoc(mt_file)

    if isdir(ref):
        for f in find_files(ref, ['csv']):

            if f.endswith(METATAB_FILE):
                continue

            if doc.find_first('Root.Datafile', value=f):
                prt("Datafile exists for '{}', ignoring".format(f))
            else:
                add_single_resource(doc, f, cache=cache)
    else:

        for c in enumerate_contents(ref, cache=cache, callback=prt):
            add_single_resource(doc, c.rebuild_url(), cache=cache)

    doc.write_csv(mt_file)


def run_row_intuit(path, cache):
    from rowgenerators import RowGenerator
    from tableintuit import RowIntuiter
    from itertools import islice
    from rowgenerators import TextEncodingError

    for encoding in ('ascii', 'utf8', 'latin1'):
        try:
            rows = list(islice(RowGenerator(url=path, encoding=encoding, cache=cache), 5000))
            return encoding, RowIntuiter().run(list(rows))
        except TextEncodingError:
            pass

    raise Exception('Failed to convert with any encoding')


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


def alt_col_name(name):
    import re
    return re.sub('_+', '_', re.sub('[^\w_]', '_', name).lower()).rstrip('_')


def process_resources(mt_file, cache):
    doc = MetatabDoc().load_csv(mt_file)

    try:
        doc['Schema'].clean()
    except KeyError:
        pass

    for t in list(doc['Resources']):  # w/o list(), will iterate over new terms

        if not t.term_is('root.datafile'):
            continue

        if t.as_dict().get('url'):
            add_resource(doc, t.as_dict()['url'], cache)

        else:
            warn("Entry '{}' on row {} is missing a url; skipping".format(t.join, t.row))

    doc.write_csv(mt_file)


type_map = {
    float.__name__: 'number',
    int.__name__: 'integer',
    six.text_type.__name__: 'string',
    six.binary_type.__name__: 'text',

}


def process_schemas(mt_file, cache):
    from rowgenerators import SourceError
    from requests.exceptions import ConnectionError

    doc = MetatabDoc().load_csv(mt_file)

    try:
        doc['Schema'].clean()
    except KeyError:
        doc.new_section('Schema', ['DataType', 'Altname', 'Description'])

    for t in doc['Resources']:

        if not t.term_is('root.datafile'):
            continue

        e = {k: v for k, v in t.properties.items() if v}

        path, name = extract_path_name(t.value)

        prt("Processing {}".format(t.value))

        rg = RowGenerator(url=path,
                          name=e.get('name'),
                          encoding=e.get('encoding', 'utf8'),
                          format=e.get('format'),
                          file=e.get('file'),
                          segment=e.get('segment'),
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

        for c in ti.to_rows():
            raw_alt_name = alt_col_name(c['header'])
            alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

            table.new_child('Column', c['header'],
                            datatype=type_map.get(c['resolved_type'], c['resolved_type']),
                            altname=alt_name)

    doc.write_csv(mt_file)


def write_excel_package(mt_file, d, cache):
    from metatab.package import ExcelPackage

    p = ExcelPackage(mt_file, callback=prt, cache=cache)

    p.save()


def write_zip_package(mt_file, d, cache):
    from metatab.package import ZipPackage

    p = ZipPackage(mt_file, callback=prt, cache=cache)

    p.save()


def write_dir_package(mt_file, d, cache):
    from metatab.package import FileSystemPackage

    p = FileSystemPackage(mt_file, callback=prt, cache=cache)

    p.save()

def write_s3_package(mt_file, url, cache):

    from metatab.package import S3Package

    p = S3Package(mt_file, callback=prt, cache=cache)

    p.save(url)



def rewrite_resource_format(mt_file):
    doc = MetatabDoc().load_csv(mt_file)

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


