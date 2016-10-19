# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

import sys


def main(sys_args):
    import argparse
    from metatab import __meta__
    from metatab.parser import TermInterpreter, TermGenerator
    from metatab.parser import CsvPathRowGenerator, DeclareTermInterpreter

    parser = argparse.ArgumentParser(
        prog='struct_tab',
        description='Simple Structured Table format parser. '.format(__meta__.__version__))

    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument('-t', '--terms', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, before interpretation')
    g.add_argument('-i', '--interp', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, after interpretation')
    g.add_argument('-j', '--json', default=False, action='store_true',
                   help='Parse a file and print out a JSON representation')
    g.add_argument('-y', '--yaml', default=False, action='store_true',
                   help='Parse a file and print out a YAML representation')

    parser.add_argument('-d', '--declare', default=False, action='store_true',
                 help='Parse a declaration file and print out declaration dict. Use -j or -y for the format')

    parser.add_argument('file', help='Path to a CSV file with STF data.')

    args = parser.parse_args(sys_args[1:])

    rg = CsvPathRowGenerator(args.file)

    term_gen = list(TermGenerator(rg))

    if args.declare:
        term_interp = DeclareTermInterpreter(term_gen)
    else:
        term_interp = TermInterpreter(term_gen)

    if args.interp:
        for t in list(term_interp):
            print(t)
        exit(0)
    elif args.terms:
        for t in term_gen:
            print(t)
        exit(0)

    dicts = term_interp.as_dict()

    if args.declare:
        term_interp.import_declare_doc(dicts)
        dicts = term_interp.declare_dict

    if args.json:
        import json
        print(json.dumps(dicts, indent=4))
    elif args.yaml:
        import yaml
        print(yaml.dump(dicts, default_flow_style=False, indent=4))

    term_interp = DeclareTermInterpreter(term_gen, False)

