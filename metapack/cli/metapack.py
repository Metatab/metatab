# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
CLI program for managing packages
"""

import json
import sys
from uuid import uuid4

import re
import six
from genericpath import isdir
from metatab import _meta, DEFAULT_METATAB_FILE, ConversionError
from metapack import MetapackDoc, Downloader
from metapack.appurl import  MetapackUrl
from metapack.jupyter.convert import convert_documentation, convert_notebook
from metapack.cli.core import prt, err, warn, dump_resource, dump_resources, metatab_info, find_files, \
    get_lib_module_dict, write_doc, datetime_now, \
    make_excel_package, make_filesystem_package, make_csv_package, make_zip_package, update_name, \
    cli_init, process_schemas, extract_path_name, PACKAGE_PREFIX, MetapackCliMemo
from metapack.util import make_metatab_file
from os import getcwd
from os.path import dirname, abspath, exists
from rowgenerators import SourceError
from rowgenerators.util import clean_cache
from rowgenerators.util import fs_join as join
from tableintuit import RowIntuitError
from appurl import parse_app_url

downloader = Downloader()

def metapack(subparsers):

    parser = subparsers.add_parser(
        'pack',
        help='Create and manipulate metatab data packages, version {}'.format(_meta.__version__),
        epilog='Cache dir: {}\n'.format(str(downloader.cache.getsyspath('/'))))

    parser.set_defaults(run_command=run_metapack)

    parser.add_argument('metatabfile', nargs='?',
                        help="Path or URL to a metatab file. If not provided, defaults to 'metadata.csv' ")

    parser.add_argument('-p', '--profile', help="Name of a BOTO or AWS credentails profile", required=False)

    parser.add_argument('--exceptions', default=False, action='store_true',
                             help='Show full stack tract for some unhandled exceptions')

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
                             help='Force some operations, like updating the name and building packages')

    build_group.add_argument('-M', '--make-package', default=False, action='store_true',
                             help='Build a package from a Jupyter notebook')

    build_group.add_argument('-D', '--make-documentation', default=False, action='store_true',
                             help='With -M, make only the documentation')

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


def run_metapack(args):


    m = MetapackCliMemo(args, downloader)

    # Maybe need to convert a notebook first
    if m.args.make_package:

        u = parse_app_url(m.mtfile_arg)

        if u.target_format != 'ipynb':
            print (u.dict)
            err("Input must be a Jupyter notebook file. Got '{}' ".format(u.target_format))

        if m.args.make_documentation:
            convert_documentation(m)
            sys.exit(0)
        else:
            convert_notebook(m)

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    if m.args.profile:
        from metatab.s3 import set_s3_profile
        set_s3_profile(m.args.profile)

    try:
        for handler in (metatab_build_handler, metatab_derived_handler, metatab_query_handler, metatab_admin_handler):
            handler(m)
    except Exception as e:
        if m.args.exceptions:
            raise e
        else:
            err(e)

    clean_cache(m.cache)

def metatab_build_handler(m):

    if m.args.create is not False:

        template = m.args.create if m.args.create else 'metatab'

        if not m.mt_file.exists():

            doc = make_metatab_file(template)

            doc['Root']['Created'] = datetime_now()

            write_doc(doc, m.mt_file)

            prt('Created', m.mt_file)
        else:
            err('File', m.mt_file, 'already exists')

    if m.args.add:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        add_resource(m.mt_file, m.args.add, cache=m.cache)


    if m.args.schemas:
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        process_schemas(m.mt_file, cache=m.cache, clean=m.args.clean)

    if m.args.datapackage:
        err('Not Implemented')
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

        from metatab.datapackage import convert_to_datapackage

        doc = MetapackDoc(m.mt_file)

        u = parse_app_url(m.mt_file)

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


def metatab_derived_handler(m, skip_if_exists=None):
    """Create local Zip, Excel and Filesystem packages

    :param m:
    :param skip_if_exists:
    :return:
    """
    from metapack.exc import PackageError

    create_list = []
    url = None

    doc = MetapackDoc(m.mt_file)

    env = get_lib_module_dict(doc)

    if (m.args.excel is not False or m.args.zip is not False or
            (hasattr(m.args, 'filesystem') and m.args.filesystem is not False) ):
        update_name(m.mt_file, fail_on_missing=False, report_unchanged=False)

    if m.args.force:
        skip_if_exists = False

    try:

        # Always create a filesystem package before ZIP or Excel, so we can use it as a source for
        # data for the other packages. This means that Transform processes and programs only need
        # to be run once.
        if any([m.args.filesystem, m.args.excel, m.args.zip]):

            _, url, created = make_filesystem_package(m.mt_file, m.package_root, m.cache, env, skip_if_exists)
            create_list.append(('fs', url, created))

            m.mt_file = url

            env = {}  # Don't need it anymore, since no more programs will be run.

        if m.args.excel is not False:
            _, url, created = make_excel_package(m.mt_file, m.package_root, m.cache, env, skip_if_exists)
            create_list.append(('xlsx', url, created))

        if m.args.zip is not False:
            _, url, created = make_zip_package(m.mt_file, m.package_root, m.cache, env, skip_if_exists)
            create_list.append(('zip', url, created))

        if m.args.csv is not False:
            _, url, created = make_csv_package(m.mt_file, m.package_root, m.cache, env, skip_if_exists)
            create_list.append(('csv', url, created))

    except PackageError as e:
        err("Failed to generate package: {}".format(e))

    return create_list


def metatab_query_handler(m):
    if m.args.resource or m.args.head:

        limit = 20 if m.args.head else None

        try:
            doc = MetapackDoc(m.mt_file, cache=m.cache)

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
        doc = MetapackDoc(m.mt_file)

        # print(doc.html)
        prt(html(doc))

    if m.args.markdown:
        from metatab.html import markdown

        doc = MetapackDoc(m.mt_file)
        prt(markdown(doc))

    if m.args.clean_cache:
        clean_cache('metapack')

    if m.args.name:
        doc = MetapackDoc(m.mt_file)
        prt(doc.find_first_value("Root.Name"))
        exit(0)


def classify_url(url):

    ss = parse_app_url(url)

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

    if isinstance(mt_file, MetapackDoc):
        doc = mt_file
    else:
        doc = MetapackDoc(mt_file)

    if not 'Resources' in doc:
        doc.new_section('Resources')

    doc['Resources'].args = [e for e in set(doc['Resources'].args + ['Name', 'StartLine', 'HeaderLines', 'Encoding']) if
                             e]

    seen_names = set()

    u = parse_app_url(ref)

    # The web and file URLs don't list the same.

    if u.proto == 'file':
        entries = u.list
    else:
        entries = [ssu for su in u.list() for ssu in su.list()]

    for e in entries:
        add_single_resource(doc, e, cache=cache, seen_names=seen_names)

    write_doc(doc, mt_file)


def add_single_resource(doc, ref, cache, seen_names):
    from metatab.util import slugify

    t = doc.find_first('Root.Datafile', value=ref)

    if t:
        prt("Datafile exists for '{}', deleting".format(ref))
        doc.remove_term(t)
    else:
        prt("Adding {}".format(ref))

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

    if False:
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

def run_row_intuit(path, cache):

    from tableintuit import RowIntuiter
    from itertools import islice
    from rowgenerators import TextEncodingError, get_generator

    for encoding in ('ascii', 'utf8', 'latin1'):
        try:

            u = parse_app_url(path)
            u.encoding = encoding

            rows = list(islice(get_generator(url=str(u),cache=cache,), 5000))
            return encoding, RowIntuiter().run(list(rows))
        except (TextEncodingError, UnicodeEncodeError) as e:
            pass

    raise RowIntuitError('Failed to convert with any encoding')



DATA_FORMATS = ('xls', 'xlsx', 'tsv', 'csv')
DOC_FORMATS = ('pdf', 'doc', 'docx', 'html')
