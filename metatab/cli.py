# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

from __future__ import print_function

import json
import sys
from uuid import uuid4

from metatab import TermParser, Term, CsvPathRowGenerator, CsvUrlRowGenerator, GenericRowGenerator
from metatab import _meta, MetatabDoc
from os.path import exists, abspath
LE = 'metadata.csv'


def prt(*args):
    print(*args)


def err(*args):
    import sys
    print("ERROR:", *args)
    sys.exit(1)


def metatab():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metatab',
        description='Simple Structured Table format parser, version {}'.format(_meta.__version__))

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

    if args.declare:
        raise NotImplementedError()

    elif args.package:
        raise NotImplementedError

    rg = GenericRowGenerator(args.file)

    term_interp = TermParser(rg)

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
        for t in term_interp:
            print(t)

    elif args.json:
        print(json.dumps(MetatabDoc(terms=term_interp).as_dict(), indent=4))

    elif args.yaml:
        import yaml
        print(yaml.safe_dump(MetatabDoc(terms=term_interp).as_dict(), default_flow_style=False, indent=4))

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
