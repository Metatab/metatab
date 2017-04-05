# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import json
import re
import sys
from genericpath import exists, isdir
from itertools import islice
from os import getcwd
from os.path import join, dirname, abspath
from uuid import uuid4
from datetime import datetime

import six

from metatab import _meta, DEFAULT_METATAB_FILE, resolve_package_metadata_url, MetatabDoc, ConversionError
from metatab.cli.core import prt, err, warn, dump_resource, dump_resources, metatab_info, find_files, \
    get_lib_module_dict, write_doc, datetime_now, \
    make_excel_package, make_filesystem_package, make_s3_package, make_csv_package, make_zip_package, update_name
from metatab.util import make_metatab_file
from rowgenerators import get_cache, RowGenerator, SelectiveRowGenerator, SourceError, Url
from rowgenerators.util import clean_cache
from tableintuit import TypeIntuiter, RowIntuitError


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

    # build_group.add_argument('-S', '--scrape',
    #                help='Similar to --add, but scrape a web page for links to data files, documentation '
    #                     'and web pages and add the links as resources ')

    # build_group.add_argument('-r', '--resources', default=False, action='store_true',
    #                    help='Rebuild the resources, intuiting rows and encodings from the URLs')


    build_group.add_argument('-s', '--schemas', default=False, action='store_true',
                             help='Rebuild the schemas for files referenced in the resource section')

    build_group.add_argument('-d', '--datapackage', action='store_true', default=False,
                             help="Write a datapackage.json file adjacent to the metatab file")

    build_group.add_argument('-u', '--update', action='store_true', default=False,
                             help="Update the Name from the Datasetname, Origin and Version terms")

    build_group.add_argument('-F', '--force', action='store_true', default=False,
                               help='Force some operations, like updating the name')

    ##
    ## Derived Package Group

    derived_group = parser.add_argument_group('Derived Packages', 'Generate other types of packages')

    derived_group.add_argument('-e', '--excel', action='store_true', default=False,
                               help='Create an excel archive from a metatab file')

    derived_group.add_argument('-z', '--zip', action='store_true', default=False,
                               help='Create a zip archive from a metatab file')

    derived_group.add_argument('-f', '--filesystem', action='store_true', default=False,
                               help='Create a filesystem archive from a metatab file')

    derived_group.add_argument('-v', '--csv', action='store_true', default=False,
                               help='Create a CSV archive from a metatab file')

    derived_group.add_argument('-s3', '--s3', action='store',
                               help='Create a filesystem archive in an S3 bucket. Argument is an S3 URL with the bucket name and '
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

    admin_group.add_argument('-n', '--name', default=False, action='store_true',
                             help="Print the name of the package")

    admin_group.add_argument('-E', '--enumerate',
                             help='Enumerate the resources referenced from a URL. Does not alter the Metatab file')

    admin_group.add_argument('--html', default=False, action='store_true',
                             help='Generate HTML documentation')

    admin_group.add_argument('--markdown', default=False, action='store_true',
                             help='Generate Markdown documentation')

    # cmd = parser.add_subparsers(title='Plugin Commands', help='Additional command supplied by plugins')
    # load_plugins(cmd)


    class MetapackCliMemo(object):
        def __init__(self, args):
            self.cwd = getcwd()
            self.args = args
            self.cache = get_cache('metapack')

            if args.metatabfile and args.metatabfile.startswith('#'):
                # It's just a fragment, default metatab file
                args.metatabfile = join(self.cwd, DEFAULT_METATAB_FILE) + args.metatabfile

            self.mtfile_arg = args.metatabfile if args.metatabfile else join(self.cwd, DEFAULT_METATAB_FILE)

            self.mtfile_url = Url(self.mtfile_arg)

            self.resource = self.mtfile_url.parts.fragment

            self.package_url, self.mt_file = resolve_package_metadata_url(self.mtfile_url.rebuild_url(False, False))


    m = MetapackCliMemo(parser.parse_args(sys.argv[1:]))

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    for handler in (metatab_build_handler, metatab_derived_handler, metatab_query_handler, metatab_admin_handler):
        handler(m)

    clean_cache(m.cache)


def metatab_build_handler(m):
    if m.args.create is not False:

        template = m.args.create if m.args.create else 'metatab'

        if not exists(m.mt_file):

            doc = make_metatab_file(template)

            doc['Root']['Identifier'] = six.text_type(uuid4())

            doc['Root']['Created'] = datetime_now()

            write_doc(doc, m.mt_file)

            prt('Created', m.mt_file)
        else:
            err('File', m.mt_file, 'already exists')

    if m.args.add:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        add_resource(m.mt_file, m.args.add, cache=m.cache)

    if False:  # m.args.resources:
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

        write_doc(doc, m.mt_file)

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
        update_name(m.mt_file, fail_on_missing=True, force=m.args.force)


def metatab_derived_handler(m, skip_if_exists=False):
    from metatab.package import PackageError

    create_list = []
    url = None

    doc = MetatabDoc(m.mt_file)
    env = get_lib_module_dict(doc)

    if (m.args.excel is not False or m.args.zip is not False or
            (hasattr(m.args, 'filesystem') and m.args.filesystem is not False) or m.args.s3):
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    try:

        if m.args.excel is not False:
            url, created = make_excel_package(m.mt_file, m.cache, env, skip_if_exists)
            create_list.append(('xlsx', url, created))

        if m.args.zip is not False:
            url, created = make_zip_package(m.mt_file, m.cache, env, skip_if_exists)
            create_list.append(('zip', url, created))

        if m.args.filesystem is not False:
            url, created = make_filesystem_package(m.mt_file, m.cache, env, skip_if_exists)
            create_list.append(('fs', url, created))

        if m.args.csv is not False:
            url, created = make_csv_package(m.mt_file, m.cache, env, skip_if_exists)
            create_list.append(('csv', url, created))

        if m.args.s3:
            url, created = make_s3_package(m.mt_file, m.args.s3, m.cache, env, skip_if_exists)
            create_list.append(('s3', url, created))

    except PackageError as e:
        err("Failed to generate package: {}".format(e))

    return create_list


def metatab_query_handler(m):
    if m.args.resource or m.args.head:

        limit = 20 if m.args.head else None

        try:
            doc = MetatabDoc(m.mt_file, cache=m.cache)
        except OSError as e:
            err("Failed to open Metatab doc: {}".format(e))
            return

        if m.resource:
            dump_resource(doc, m.resource, limit)
        else:
            dump_resources(doc)


def metatab_admin_handler(m):
    if m.args.enumerate:

        from metatab.util import enumerate_contents

        specs = list(enumerate_contents(m.args.enumerate, m.cache, callback=prt))

        for s in specs:
            prt(classify_url(s.url), s.target_format, s.url, s.target_segment)

    if m.args.html:
        from metatab.html import html
        doc = MetatabDoc(m.mt_file)

        # print(doc.html)
        prt(html(doc))

    if m.args.markdown:
        from metatab.html import markdown

        doc = MetatabDoc(m.mt_file)
        prt(markdown(doc))

    if m.args.clean_cache:
        clean_cache('metapack')

    if m.args.name:
        doc = MetatabDoc(m.mt_file)
        prt(doc.find_first_value("Root.Name"))
        exit(0)


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


def add_resource(mt_file, ref, cache):
    """Add a resources entry, downloading the intuiting the file, replacing entries with
    the same reference"""
    from metatab.util import enumerate_contents

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

    write_doc(doc, mt_file)


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

        if 'schema' in e:
            schema_name = e['schema']
        else:
            schema_name = e['name']

        schema_term = doc.find_first(term='Table', value=schema_name, section='Schema')

        if schema_term:
            prt("Found table for '{}'; skipping".format(schema_name))
            continue

        path, name = extract_path_name(t.value)

        prt("Processing {}".format(t.value))

        rg = RowGenerator(url=path,
                          name=e['name'],
                          encoding=e.get('encoding', 'utf8'),
                          target_format=e.get('format'),
                          target_file=e.get('file'),
                          target_segment=e.get('segment'),
                          cache=cache,
                          working_dir=doc.doc_dir,
                          generator_args=dict(t.properties.items())
                          )

        si = SelectiveRowGenerator(islice(rg, 20),
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

        table = doc['Schema'].new_term('Table', schema_name)

        prt("Adding table '{}' ".format(schema_name))

        for i, c in enumerate(ti.to_rows()):
            raw_alt_name = alt_col_name(c['header'], i)
            alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

            table.new_child('Column', c['header'],
                            datatype=type_map.get(c['resolved_type'], c['resolved_type']),
                            altname=alt_name)

    write_doc(doc, mt_file)


def add_single_resource(doc, ref, cache, seen_names):
    from metatab.util import slugify

    t = doc.find_first('Root.Datafile', value=ref)

    if t:
        prt("Datafile exists for '{}', deleting".format(ref))
        doc.remove_term(t)

    term_name = classify_url(ref)

    path, name = extract_path_name(ref)

    # If the name already exists, try to create a new one.
    # 20 attempts ought to be enough.
    if name in seen_names:
        base_name = re.sub(r'-?\d+$', '', name)

        for i in range(1, 20):
            name = "{}-{}".format(base_name, i)
            if name not in seen_names:
                break

    seen_names.add(name)

    encoding = start_line = None
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

    except Exception as e:
        warn("Error: '{}'; {}".format(path, e))

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

    return re.sub('_+', '_', re.sub('[^\w_]', '_', str(name)).lower()).rstrip('_')


def run_row_intuit(path, cache):
    from rowgenerators import RowGenerator
    from tableintuit import RowIntuiter
    from itertools import islice
    from rowgenerators import TextEncodingError

    for encoding in ('ascii', 'utf8', 'latin1'):
        try:
            rows = list(islice(RowGenerator(url=path,
                                            encoding=encoding,
                                            cache=cache,
                                            ), 5000))
            return encoding, RowIntuiter().run(list(rows))
        except (TextEncodingError, UnicodeEncodeError) as e:
            pass

    raise RowIntuitError('Failed to convert with any encoding')


DATA_FORMATS = ('xls', 'xlsx', 'tsv', 'csv')
DOC_FORMATS = ('pdf', 'doc', 'docx', 'html')
type_map = {
    float.__name__: 'number',
    int.__name__: 'integer',
    six.text_type.__name__: 'string',
    six.binary_type.__name__: 'text',

}
