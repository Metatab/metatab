import sys
from genericpath import exists
from uuid import uuid4

import six

from metatab import _meta
from metatab.util import make_metatab_file
from rowgenerators import Url

def prt(*args, **kwargs):
    print(*args, **kwargs)


def warn(*args, **kwargs):
    print('WARN:', *args, file=sys.stderr, **kwargs)


def err(*args, **kwargs):
    import sys
    print("ERROR:", *args, file=sys.stderr, **kwargs)
    sys.exit(1)


def load_plugins(parser):
    import metatab_plugins._plugins as mtp

    for p in mtp.metatab_plugins_list:
        p(parser)


def metatab_info(cache):
    prt('Version  : {}'.format(_meta.__version__))
    prt('Cache dir: {}'.format(str(cache.getsyspath('/'))))

    print(__file__)


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


def get_lib_module_dict(doc):
    from os.path import dirname, abspath
    from importlib import import_module
    import sys

    u = Url(doc.ref)
    if u.proto == 'file':

        # Add the dir with the metatab file to the system path
        sys.path.append(dirname(abspath(u.parts.path)))

        try:
            m = import_module("lib")
            return {k: v for k, v in m.__dict__.items() if k in m.__all__}
        except ImportError:
            return {}

    else:
        return {}


def dump_resources(doc):
    for r in doc.resources():
        print(r.name, r.resolved_url)


def dump_resource(doc, name, lines=None):
    import unicodecsv as csv
    import sys
    from itertools import islice
    from tabulate import tabulate
    from rowpipe.exceptions import CasterExceptionError

    r = doc.resource(name=name, env=get_lib_module_dict(doc))

    if not r:
        err("Did not get resource for name '{}'".format(name))

    # WARNING! This code will not generate errors if line is set ( as for the -H
    # option because the errors are tansfered from the row pipe to the resource after the
    # iterator is exhausted


    try:
        gen = islice(r, int(r.startline), lines)
    except (ValueError, AttributeError):
        gen = islice(r, 1, lines)


    try:
        if lines and lines <= 20:
            print(tabulate(list(gen), list(r.headers())))

        else:

            w = csv.writer(sys.stdout if six.PY2 else sys.stdout.buffer)

            if r.headers():
                w.writerow(r.headers())
            else:
                warn("No headers for resource '{}'; have schemas been generated? ".format(name))

            for row in gen:
                w.writerow(row)

    except CasterExceptionError as e:  # Really bad errors, not just casting problems.
        err(e)

    for col, errors in r.errors.items():
        warn("Errors in casting column '{}' in resource '{}' ".format(col, r.name))
        for e in errors:
            warn("    ", e)


def dump_schema(doc, name):
    from tabulate import tabulate

    t = get_table(doc, name)

    rows = []
    header = 'name altname datatype description'.split()
    for c in t.children:
        cp = c.properties
        rows.append([cp.get(h) for h in header])

    prt(tabulate(rows, header))


def get_table(doc, name):
    t = doc.find_first('Root.Table', value=name)

    if not t:

        table_names = ["'" + t.value + "'" for t in doc.find('Root.Table')]

        if not table_names:
            table_names = ["<No Tables>"]

        err("Did not find schema for table name '{}' Tables are: {}"
            .format(name, " ".join(table_names)))

    return t