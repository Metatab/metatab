# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

from __future__ import print_function
import sys


def metatab():
    import argparse
    import sys
    from metatab import __meta__
    from metatab import TermInterpreter, TermGenerator, Term, CsvPathRowGenerator, CsvUrlRowGenerator

    parser = argparse.ArgumentParser(
        prog='metatab',
        description='Simple Structured Table format parser, version {}'.format(__meta__.__version__))

    g = parser.add_mutually_exclusive_group(required=True)
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

    parser.add_argument('file', help='Path to a CSV file with STF data.')

    args = parser.parse_args(sys.argv[1:])

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

    term_interp = TermInterpreter(term_gen)

    if args.show_declaration:
        term_interp.install_declare_terms()

    if args.interp:
        for t in list(term_interp):
            print(t)
        exit(0)
    elif args.terms:
        for t in term_gen:
            print(t)
        exit(0)

    term_interp.run();

    if args.show_declaration:
        declare_ti = TermInterpreter([])
        declare_ti.import_declare_doc(term_interp.as_dict())
        dicts = declare_ti.declare_dict
    else:
        dicts = term_interp.as_dict()

    if args.json:
        import json
        print(json.dumps(dicts, indent=4))
    elif args.yaml:
        import yaml
        print(yaml.safe_dump(dicts, default_flow_style=False, indent=4))

def find_files(base_path, types):
    from os import walk
    from os.path import join, splitext

    for root, dirs, files in walk(base_path):

        for f in files:
            if f.startswith('_'):
                continue
            b, ext = splitext(f)
            if ext[1:] in types:
                yield join(root,  f)

METATAB_FILE = 'metadata.csv'

def prt(*args):
    print(*args)

def metapack():
    import argparse
    from os import getcwd
    from os.path import splitext, exists, join
    import sys
    from metatab.metapack import make_dir_structure, make_metatab_file
    from metatab import __meta__, MetatabDoc
    from uuid import uuid4

    parser = argparse.ArgumentParser(
        prog='metapack',
        description='Create metatab data packages, version {}'.format(__meta__.__version__))

    parser.add_argument('-z', '--zip', default=False, action='store_true',
                        help='Create a zip archive from a metapack file')

    parser.add_argument('-e', '--excel', default=False, action='store_true',
                        help='Create an excel archive from a metapack file')

    parser.add_argument('-m', '--metatab', default=False, action='store_true',
                        help='Create a metatab file from for tabular data files in current and subdirectories. '
                             ' Also merges with existing metatab file, if specified')

    args = parser.parse_args(sys.argv[1:])

    d = getcwd()

    make_dir_structure(d)

    if exists(join(d, METATAB_FILE)):
        doc = MetatabDoc().load_csv(join(d, METATAB_FILE))
    else:
        doc = make_metatab_file(d)

    doc['Root']['Identifier'] = str(uuid4())

    try:
        del doc['Schema']
    except KeyError:
        pass

    try:
        del doc['Resources']
    except KeyError:
        pass

    r = doc.get_or_new_section('Resources',['Url', 'StartLine','HeaderLines','Description'])

    s = doc.get_or_new_section('Schema', ['DataType', 'AltName', 'Description'])

    from rowgenerators import RowGenerator
    from os.path import join
    from tableintuit import RowIntuiter, TypeIntuiter, SelectiveRowGenerator
    from itertools import islice

    for f in find_files(d, ['csv']):

        prt("Processing ", f)
        if f.endswith(METATAB_FILE):
            continue

        path = f.replace(d, '').strip('/')
        name,_ = splitext(path)

        rows = list(islice(RowGenerator(url=join(d, f), encoding='latin1'),5000))
        ri = RowIntuiter().run(list(rows))

        ti = TypeIntuiter().run(SelectiveRowGenerator(rows, **ri.spec))

        r.new_term('Datafile', name, url=path,
                   startline=ri.start_line,
                   headerlines=','.join(str(e) for e in ri.header_lines))

        table = s.new_term('Table',name)

        for c in ti.to_rows():
            table.new_child('Column',c['header'], datatype=c['resolved_type'])


    doc.write_csv(join(d, METATAB_FILE))







