# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

from __future__ import print_function

import json
import sys
from uuid import uuid4

from metatab import TermParser, TermGenerator, Term, CsvPathRowGenerator, CsvUrlRowGenerator
from metatab import __meta__, MetatabDoc
from metatab.metapack import make_dir_structure, make_metatab_file
from os import getcwd
from os.path import exists, join


def metatab():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metatab',
        description='Simple Structured Table format parser, version {}'.format(__meta__.__version__))

    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument('-c', '--create',  action='store', nargs='?', default=False,
                   help="Create a new metatab file, from named template. With no argument, uses the 'metatab' template ")
    g.add_argument('-t', '--terms', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, before interpretation')
    g.add_argument('-i', '--interp', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, after interpretation')
    g.add_argument('-j', '--json', default=False, action='store_true',
                   help='Parse a file and print out a JSON representation')
    g.add_argument('-p', '--package', default=False, action='store_true',
                   help='Produce a datapackage.json file')
    g.add_argument('-y', '--yaml', default=False, action='store_true',
                   help='Parse a file and print out a YAML representation')

    parser.add_argument('-d', '--show-declaration', default=False, action='store_true',
                        help='Parse a declaration file and print out declaration dict. Use -j or -y for the format')

    parser.add_argument('-D', '--declare', help='Parse and incorporate a declaration before parsing the file.' +
                                                ' (Adds the declaration to the start of the file as the first term. )')

    g.add_argument('-V', '--version', default=False, action='store_true',
                   help='Display the package version and exit')

    parser.add_argument('file', help='Path to a Metatab file')

    args = parser.parse_args(sys.argv[1:])

    if args.create:
        new_metatab_file(args.file, args.create)
        exit(0)

    if args.file.startswith('http'):
        rg = CsvUrlRowGenerator(args.file)
    else:
        rg = CsvPathRowGenerator(args.file)

    term_gen = list(TermGenerator(rg))


    if args.declare:
        term_gen = [Term('Root.Declare', args.declare, [], row=0, col=0, file_name='<commandline>')] + term_gen

    if args.package:
        term_gen = [Term('Root.Declare',
                         'https://raw.githubusercontent.com/CivicKnowledge/metatab/master/config/datapackage.csv',
                         [], row=0, col=0, file_name='<commandline>')
                    ] + term_gen

    term_interp = TermParser(term_gen)
    doc = MetatabDoc(terms=term_interp)

    if args.show_declaration:
        term_interp.install_declare_terms()
        declare_ti = TermParser([])
        declare_ti.import_declare_doc(term_interp.as_dict())
        dicts = declare_ti.declare_dict
        print(json.dumps(dicts, indent=4))
        exit(0)

    if args.interp:
        for t in list(term_interp):
            print(t)

    elif args.terms:
        for t in term_gen:
            print(t)

    elif args.json:
        print(json.dumps(doc.as_dict(), indent=4))

    elif args.yaml:
        import yaml
        print(yaml.safe_dump(doc.as_dict(), default_flow_style=False, indent=4))

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


METATAB_FILE = 'metadata.csv'


def prt(*args):
    print(*args)


def err(*args):
    import sys
    print("ERROR:", *args)
    sys.exit(1)


def metapack():
    import argparse

    parser = argparse.ArgumentParser(
        prog='metapack',
        description='Create metatab data packages, version {}'.format(__meta__.__version__))

    parser.add_argument('-i', '--init', action='store', nargs='?', default=False,
                        help='Set the cache directory for downloads and building packages')

    parser.add_argument('-a', '--add', default=False,
                        help='Add a file or url to the resources')

    parser.add_argument('-r', '--resources', action='store', nargs='?', default=False,
                        help='Rebuild the resources section of a metatab file with files in a directory')

    parser.add_argument('-s', '--schemas', default=False, action='store_true',
                        help='Rebuild the schemas for files referenced in the resource section')

    parser.add_argument('-e', '--excel', action='store', nargs='?', default=False,
                        help='Create an excel archive from a metatab file')

    parser.add_argument('-z', '--zip', action='store', nargs='?', default=False,
                        help='Create a zip archive from a metatab file')

    parser.add_argument('-R', '--resource-format', action='store_true', default=False,
                        help="Re-write the metatab file in 'Resource' format ")

    parser.add_argument('metatabfile', nargs='?')

    args = parser.parse_args(sys.argv[1:])

    d = getcwd()

    cache = get_cache(d)

    prt('Cache dir: {}'.format(str(cache)))

    mt_file = args.metatabfile if args.metatabfile else join(d, METATAB_FILE)

    if args.init is not  False:
        init_metatab(mt_file, args.init)

    if args.resources is not False:
        process_resources(mt_file, args.resources)

    if args.schemas:
        process_schemas(mt_file)

    if args.add:
        add_resource(mt_file, args.add, cache=cache)

    if args.excel is not False:
        write_excel_package(mt_file, args.excel, cache=cache)

    if args.zip is not  False:
        write_zip_package(mt_file, args.zip, cache=cache)

    if args.resource_format:
        rewrite_resource_format(mt_file)


def get_cache(d):
    from fs.opener import fsopendir
    from metatab.metapack import make_dir_structure

    make_dir_structure(d)

    return fsopendir(join(d, '_metapack', 'download'))


def init_metatab(mt_file, d):

    d = d if d is not None else getcwd()

    prt("Initializing '{}'".format(d))

    make_dir_structure(d)

    if not exists(mt_file):
        doc = make_metatab_file()

        doc['Root']['Identifier'] = str(uuid4())

        doc.write_csv(mt_file)
    else:
        prt("Doing nothing; file '{}' already exists".format(mt_file))


def process_resources(mt_file, d):
    from os import getcwd
    from os.path import join
    from metatab import MetatabDoc

    d = d if d is not None else getcwd()

    mt_file = mt_file if mt_file else join(getcwd(), METATAB_FILE)

    doc = MetatabDoc().load_csv(mt_file)

    doc['Schema'].clean()
    doc['Resources'].clean()

    from os.path import splitext, basename

    cache = get_cache(d)

    for f in find_files(d, ['csv']):

        if f.endswith(METATAB_FILE):
            continue

        path = f.replace(d, '').strip('/')
        name = basename(splitext(path)[0])

        prt("Processing {}".format(path))

        add_resource_term(path, doc['Resources'], cache=cache)

    doc.write_csv(mt_file)


def run_row_intuit(path, cache):
    from rowgenerators import RowGenerator
    from tableintuit import RowIntuiter
    from itertools import islice

    for encoding in ('ascii', 'utf8', 'latin1'):
        try:
            rows = list(islice(RowGenerator(url=path, encoding=encoding, cache=cache), 5000))
            return encoding, RowIntuiter().run(list(rows))
        except UnicodeDecodeError:
            pass

    raise Exception('Failed to convert with any encoding')


def extract_path_name(ref):
    from os.path import splitext, basename, abspath
    from rowgenerators.util import parse_url_to_dict

    uparts = parse_url_to_dict(ref)

    if not uparts['scheme']:
        path = abspath(ref)
        name = basename(splitext(path)[0])
    else:
        path = ref
        name = basename(splitext(uparts['path'])[0])

    return path, name


def add_resource_term(ref, section, cache):
    path, name = extract_path_name(ref)

    encoding, ri = run_row_intuit(path, cache)

    return section.new_term('Datafile', ref, name=name,
                            startline=ri.start_line,
                            headerlines=','.join(str(e) for e in ri.header_lines),
                            encoding=encoding)


def add_resource(mt_file, ref, cache):

    doc = MetatabDoc().load_csv(mt_file)

    t = doc.find_first('Root.Datafile', value=ref)

    if t:
        doc.remove_term(t)

    add_resource_term(ref, doc['Resources'], cache=cache)

    doc.write_csv(mt_file)


def alt_col_name(name):
    import re
    return re.sub('_+', '_', re.sub('[^\w_]', '_', name).lower()).rstrip('_')


def process_schemas(mt_file):
    from rowgenerators import RowGenerator
    from tableintuit import TypeIntuiter, SelectiveRowGenerator
    from metatab import MetatabDoc
    from itertools import islice

    doc = MetatabDoc().load_csv(mt_file)

    doc['Schema'].clean()

    for t in doc['Resources']:
        e = t.as_dict()

        path, name = extract_path_name(e['url'])

        slice = islice(RowGenerator(url=path, encoding=e.get('encoding', 'utf8')), 5000)

        si = SelectiveRowGenerator(slice,
                                   headers=[int(i) for i in e.get('headerlines', '0').split(',')],
                                   start=e.get('startline', 1))

        ti = TypeIntuiter().run(si)

        table = doc['Schema'].new_term('Table', e['name'])

        for c in ti.to_rows():
            raw_alt_name = alt_col_name(c['header'])
            alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

            table.new_child('Column', c['header'],
                            datatype=c['resolved_type'], altname=alt_name)

    doc.write_csv(mt_file)


def write_excel_package(mt_file, d, cache):
    from metatab.excel import ExcelPackage
    from metatab import MetatabDoc

    d = d if d is not None else getcwd()

    in_doc = MetatabDoc().load_csv(mt_file)

    name = in_doc.find_first_value('root.name')

    if not name:
        err("Input metadata must define a package name in the Root.Name term")

    ep = ExcelPackage(join(d,name + '.xls'))

    ep.copy_section('root', in_doc)

    table_schemas = {t.value: t.as_dict()['column'] for t in in_doc['schema']}
    file_resources = [fr.as_dict() for fr in in_doc['resources']]

    if len(table_schemas) == 0:
        err("Cant create package without table schemas")

    for resource in file_resources:
        prt("Processing {}".format(resource['name']))
        try:
            columns = table_schemas[resource['name']]
        except KeyError:
            prt("WARN: Didn't get schema for table '{}', skipping".format(resource['name']))
            continue

        ep.add_data_file(resource['url'], resource['name'], resource.get('description'),
                         columns, int(resource.get('startline', 1))
                         , resource.get('encoding', 'latin1'),
                         cache=cache)

    ep.save()


def write_zip_package(mt_file, d, cache):
    from metatab.zip import ZipPackage
    from metatab import MetatabDoc

    d = d if d is not None else getcwd()

    in_doc = MetatabDoc().load_csv(mt_file)

    name = in_doc.find_first_value('root.name')

    if not name:
        err("Input metadata must define a package name in the Root.Name term")

    zp = ZipPackage(in_doc, d, cache)

    return

    zp.save()

def rewrite_resource_format(mt_file):

    doc = MetatabDoc().load_csv(mt_file)

    if 'schema' in doc:
        table_schemas = {t.value: t.as_dict() for t in doc['schema']}
        del doc['schema']

        for resource in doc['resources']:
            s = resource.new_child('Schema','')
            for column in table_schemas.get(resource.get_child_value('name'), {})['column']:
                c = s.new_child('column', column['name'])

                for k, v in column.items():
                    if k != 'name':
                        c.new_child(k, v)


    doc.write_csv(mt_file)
