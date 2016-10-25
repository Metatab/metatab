# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

import sys


def main():
    import argparse
    import sys
    from metatab import __meta__
    from metatab.parser import TermInterpreter, TermGenerator, Term
    from metatab.parser import CsvPathRowGenerator

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

    parser.add_argument('-d', '--show-declaration', default=False, action='store_true',
                 help='Parse a declaration file and print out declaration dict. Use -j or -y for the format')

    parser.add_argument('-D', '--declare', help='Parse and incorporate a declaration before parsing the file.'+
                        ' (Adds the declaration to the start of the file as the first term. )')

    parser.add_argument('file', help='Path to a CSV file with STF data.')

    args = parser.parse_args(sys.argv[1:])

    rg = CsvPathRowGenerator(args.file)

    term_gen = list(TermGenerator(rg))

    if args.declare:
        term_gen = [Term('Root.Declare',args.declare,[],row=0, col=0, file_name='<commandline>')] + term_gen

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



