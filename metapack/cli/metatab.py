# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for managing Metatab files
"""


import json
import sys

from metatab import _meta, DEFAULT_METATAB_FILE, resolve_package_metadata_url, MetatabDoc
from metatab.cli.core import prt, new_metatab_file, err, dump_resource, dump_resources, dump_schema, cli_init
from rowgenerators import get_cache, Url
from rowgenerators.util import clean_cache



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
        clean_cache(cache)

    if args.create is not False:
        new_metatab_file(args.file, args.create)
        exit(0)

    if args.resource or args.head:

        limit = 20 if args.head else None

        u = Url(args.file)
        resource = u.parts.fragment
        metadata_url = u.rebuild_url(False, False)

        package_url, metadata_url = resolve_package_metadata_url(metadata_url)

        try:
            doc = MetatabDoc(metadata_url, cache=cache)
        except OSError as e:
            err("Failed to open Metatab doc: {}".format(e))
            return # Never reached

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
            raise
            err("Failed to open '{}': {}".format(metadata_url, e))

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