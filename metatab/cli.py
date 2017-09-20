# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for managing Metatab files
"""

import json
import sys
from genericpath import exists

from metatab._meta import __version__
from metatab import  DEFAULT_METATAB_FILE, MetatabDoc
from appurl import parse_app_url
from appurl.util import get_cache, clean_cache
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
        description='Matatab file parser, version {}.'.format(__version__),
        epilog='Cache dir: {}\n'.format(str(cache.getsyspath('/') ) ))

    parser.add_argument('-C', '--clean-cache', default=False, action='store_true',
                        help="Clean the download cache")

    g = parser.add_mutually_exclusive_group(required=True)

    g.add_argument('-c', '--create', action='store', nargs='?', default=False,
                   help="Create a new metatab file, from named template. With no argument, uses the 'metatab' template ")

    g.add_argument('-t', '--terms', default=False, action='store_true',
                   help='Parse a file and print out the stream of terms, before interpretation')

    g.add_argument('-j', '--json', default=False, action='store_true',
                   help='Parse a file and print out a JSON representation')

    g.add_argument('-y', '--yaml', default=False, action='store_true',
                   help='Parse a file and print out a YAML representation')

    #parser.add_argument('-d', '--show-declaration', default=False, action='store_true',
    #                    help='Parse a declaration file and print out declaration dict. Use -j or -y for the format')

    #parser.add_argument('-D', '--declare', help='Parse and incorporate a declaration before parsing the file.' +
    #                                            ' (Adds the declaration to the start of the file as the first term. )')

    parser.add_argument('file', nargs='?', default=DEFAULT_METATAB_FILE, help='Path to a Metatab file')

    cli_init()

    args = parser.parse_args(sys.argv[1:])

    # Specing a fragment screws up setting the default metadata file name
    if args.file.startswith('#'):
        args.file = DEFAULT_METATAB_FILE + args.file

    if args.clean_cache:
        clean_cache(cache)

    if args.create is not False:
        if new_metatab_file(args.file, args.create):
            prt("Created ", args.file)
        else:
            warn("File",args.file,'already exists.')

        exit(0)

    metadata_url = parse_app_url(args.file)
    try:
        doc = MetatabDoc(metadata_url, cache=cache)
    except IOError as e:

        err("Failed to open '{}': {}".format(metadata_url, e))

    if args.terms:
        for t in doc._term_parser:
            print(t)

    elif args.json:
        print(json.dumps(doc.as_dict(), indent=4))

    elif args.yaml:
        import yaml
        print(yaml.safe_dump(doc.as_dict(), default_flow_style=False, indent=4))

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
