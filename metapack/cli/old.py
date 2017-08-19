# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

from __future__ import print_function

from os.path import exists
from uuid import uuid4

from metatab.cli.core import prt
from metatab.cli.metapack import classify_url
from metatab.doc import MetatabDoc
from metatab.util import make_metatab_file


# Change the row cache name


def init_metatab(mt_file, alt_mt_file):
    mt_file = alt_mt_file if alt_mt_file else mt_file

    prt("Initializing '{}'".format(mt_file))

    if not exists(mt_file):
        doc = make_metatab_file()

        doc['Root']['Identifier'] = str(uuid4())

        doc.write_csv(mt_file)
    else:
        prt("Doing nothing; file '{}' already exists".format(mt_file))


def scrape_page(mt_file, url):
    from .util import scrape_urls_from_web_page

    doc = MetatabDoc(mt_file)

    doc['resources'].new_term('DownloadPage', url)

    d = scrape_urls_from_web_page(url)

    for k, v in d['sources'].items():
        doc['Resources'].new_term('DataFile', v['url'], description=v.get('description'))

    for k, v in d['external_documentation'].items():
        term_name = classify_url(v['url'])
        doc['Documentation'].new_term(term_name, v['url'], description=v.get('description'))

    doc.write_csv(mt_file)


def rewrite_resource_format(mt_file):
    doc = MetatabDoc(mt_file)

    if 'schema' in doc:
        table_schemas = {t.value: t.as_dict() for t in doc['schema']}
        del doc['schema']

        for resource in doc['resources']:
            s = resource.new_child('Schema', '')
            for column in table_schemas.get(resource.find_value('name'), {})['column']:
                c = s.new_child('column', column['name'])

                for k, v in column.items():
                    if k != 'name':
                        c.new_child(k, v)

    doc.write_csv(mt_file)


