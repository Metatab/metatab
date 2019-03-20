# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for managing Metatab files
"""

import json
import sys
from genericpath import exists

from metatab import  DEFAULT_METATAB_FILE, MetatabDoc, parse_app_url
from rowgenerators.util import get_cache, clean_cache
from os.path import dirname
from rowgenerators.util import fs_join as join

import logging

logger = logging.getLogger('user')
logger_err = logging.getLogger('cli-errors')
debug_logger = logging.getLogger('debug')

cache = get_cache()

def metatab():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metatab',
        description='Matatab file parser',
        epilog='Cache dir: {}\n'.format(str(cache.getsyspath('/') ) ))

    g = parser.add_mutually_exclusive_group()

    g.add_argument('-C', '--create', action='store', nargs='?', default=False,
                   help="Create a new metatab file, from named template. With no argument, uses the 'metatab' template ")

    g.add_argument('-t', '--terms', default=False, action='store_const', dest='out_type', const='terms',
                   help='Parse a file and print out the stream of terms, before interpretation')

    g.add_argument('-j', '--json', default=False, action='store_const', dest='out_type', const='json',
                   help='Parse a file and print out a JSON representation')

    g.add_argument('-y', '--yaml', default=False, action='store_const', dest='out_type', const='yaml',
                   help='Parse a file and print out a YAML representation')

    g.add_argument('-l', '--line', default=False, action='store_const', dest='out_type', const='line',
                   help='Parse a file and print out a Metatab Line representation')

    g.add_argument('-c', '--csv', default=False, action='store_const', dest='out_type', const='csv',
                   help='Parse a file and print out a Metatab Line representation')

    g.add_argument('-p', '--prety', default=False, action='store_const', dest='out_type', const='prety',
                   help='Pretty print the python Dict representation ')

    parser.add_argument('-W', '--write-in-place',
                   help='When outputting as yaml, json, csv or line, write the file instead of printing it, '
                        'to a file with same base name and appropriate extension ', action='store_true')

    parser.set_defaults(out_type='csv')

    parser.add_argument('-f', '--find-first',
                   help='Find and print the first value for a fully qualified term name')

    parser.add_argument('-d', '--show-declaration', default=False, action='store_true',
                        help='Parse a declaration file and print out declaration dict. Use -j or -y for the format')

    parser.add_argument('file', nargs='?', default=DEFAULT_METATAB_FILE, help='Path to a Metatab file')

    cli_init()

    args = parser.parse_args(sys.argv[1:])

    # Specing a fragment screws up setting the default metadata file name
    if args.file.startswith('#'):
        args.file = DEFAULT_METATAB_FILE + args.file

    if args.create is not False:
        if new_metatab_file(args.file, args.create):
            prt("Created ", args.file)
        else:
            warn("File",args.file,'already exists.')

        exit(0)

    metadata_url = parse_app_url(args.file, proto='metatab')
    try:
        doc = MetatabDoc(metadata_url, cache=cache)
    except IOError as e:

        err("Failed to open '{}': {}".format(metadata_url, e))

    def write_or_print(t):
        from pathlib import Path

        if metadata_url.scheme != 'file':
            err("Can only use -w with local files")
            return

        ext = 'txt' if args.out_type == 'line' else args.out_type

        if args.write_in_place:
            with metadata_url.fspath.with_suffix('.'+ext).open('w') as f:
                f.write(t)
        else:
            print(t)



    if args.show_declaration:

        decl_doc = MetatabDoc('', cache=cache, decl=metadata_url.path)

        d = {
            'terms': decl_doc.decl_terms,
            'sections': decl_doc.decl_sections
        }

        if args.out_type == 'json':
            print(json.dumps(d, indent=4))

        elif args.out_type == 'yaml':
            import yaml
            print(yaml.safe_dump(d, default_flow_style=False, indent=4))

    elif args.find_first:

        t = doc.find_first(args.find_first)
        print(t.value)


    elif args.out_type == 'terms':
        for t in doc._term_parser:
            print(t)

    elif args.out_type == 'json':
        write_or_print(json.dumps(doc.as_dict(), indent=4))

    elif args.out_type == 'yaml':
        import yaml
        from collections import OrderedDict

        def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
            class OrderedDumper(Dumper):
                pass

            def _dict_representer(dumper, data):
                return dumper.represent_mapping(
                    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                    data.items())

            OrderedDumper.add_representer(OrderedDict, _dict_representer)
            return yaml.dump(data, stream, OrderedDumper, **kwds)

        write_or_print(ordered_dump(doc.as_dict(), default_flow_style=False, indent=4, Dumper=yaml.SafeDumper))

    elif args.out_type == 'line':
        write_or_print(doc.as_lines())

    elif args.out_type == 'csv':
        write_or_print(doc.as_csv())

    elif args.out_type == 'prety':
        from pprint import pprint
        pprint(doc.as_dict())

    exit(0)





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


def make_metatab_file(template='metatab'):
    import metatab.templates as tmpl

    template_path = join(dirname(tmpl.__file__),template+'.csv')

    doc = MetatabDoc(template_path)

    return doc



def new_metatab_file(mt_file, template):
    template = template if template else 'metatab'

    if not exists(mt_file):
        doc = make_metatab_file(template)

        doc.write_csv(mt_file)

        return True

    else:

        return False


def get_table(doc, name):
    t = doc.find_first('Root.Table', value=name)

    if not t:

        table_names = ["'" + t.value + "'" for t in doc.find('Root.Table')]

        if not table_names:
            table_names = ["<No Tables>"]

        err("Did not find schema for table name '{}' Tables are: {}"
            .format(name, " ".join(table_names)))

    return t
