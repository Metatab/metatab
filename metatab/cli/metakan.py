# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

import mimetypes
import sys
from os import getenv, getcwd
from os.path import join, basename

from metatab import _meta, DEFAULT_METATAB_FILE, resolve_package_metadata_url, MetatabDoc, open_package
from metatab.cli.core import prt, err, S3Bucket, metatab_info
from rowgenerators import get_cache, Url
from .metapack import metatab_derived_handler


def metakan():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metakan',
        description='CKAN management of Metatab packages, version {}'.format(_meta.__version__),
         )

    parser.add_argument('-i', '--info', default=False, action='store_true',
                   help="Show configuration information")

    parser.add_argument('-c', '--ckan', help="URL for CKAN instance")

    parser.add_argument('-a', '--api', help="CKAN API Key")

    parser.add_argument('metatabfile', nargs='?', default=DEFAULT_METATAB_FILE, help='Path to a Metatab file')

    class MetapackCliMemo(object):
        def __init__(self, args):
            self.cwd = getcwd()
            self.args = args
            self.cache = get_cache('metapack')

            self.mtfile_arg = args.metatabfile if args.metatabfile else join(self.cwd, DEFAULT_METATAB_FILE)

            self.mtfile_url = Url(self.mtfile_arg)
            self.resource = self.mtfile_url.parts.fragment

            self.package_url, self.mt_file = resolve_package_metadata_url(self.mtfile_url.rebuild_url(False, False))

            self.api_key = self.args.api or getenv('METAKAN_API_KEY')

            self.ckan_url = self.args.ckan or getenv('METAKAN_CKAN_URL')

            if not self.ckan_url:
                err("Set the --ckan option or the METAKAN_CKAN_URL env var to set the URL of a ckan instance")

            if not self.api_key:
                err("Set the --api option METAKAN_API_KEY env var  with the API key to a CKAN instance")

    m = MetapackCliMemo(parser.parse_args(sys.argv[1:]))

    if m.args.info:
        metatab_info(m.cache)
        exit(0)

    send_to_ckan(m)

    exit(0)


def send_to_ckan(m):
    from ckanapi import RemoteCKAN, NotFound

    try:
        doc = MetatabDoc(m.mt_file, cache=m.cache)
    except IOError as e:
        err("Failed to open metatab '{}': {}".format(m.mt_file, e))

    c = RemoteCKAN(m.ckan_url, apikey=m.api_key)

    identifier = doc.find_first_value('Root.Identitfier')
    name = doc.find_first('Root.Name')

    ckan_name = name.value.replace('.','-')

    try:
        pkg = c.action.package_show(name_or_id=ckan_name)
        prt("Updating CKAN dataset for '{}'".format(ckan_name))
    except NotFound:
        pkg = c.action.package_create(name=ckan_name, package_id=identifier)
        prt("Adding CKAN dataset for '{}'".format(ckan_name))

    pkg['title'] = doc.find_first_value('Root.Title')
    pkg['notes'] = doc.markdown #doc.find_first_value('Root.Description')
    pkg['version'] = name.properties.get('version')

    extras = []

    for t in doc.find('*.*', section='Root'):
        if not t.term_is('Root.Distribution'):
            extras.append({'key':t.qualified_term, 'value':t.value})

    for t in name.children:
        extras.append({'key': t.qualified_term, 'value': t.value})

    pkg['extras'] = extras

    #import json
    #print(json.dumps(pkg, indent=4))

    resources = []

    for d in doc.find("Root.Distribution"):

        package_url, metadata_url = resolve_package_metadata_url(d.value)

        u = Url(metadata_url)

        if u.resource_format == 'zip':
            d = dict(
                url=package_url,
                name=basename(package_url),
                format='ZIP',
                mimetype=mimetypes.guess_type(package_url)[0],
                description='ZIP version of package'
            )
            resources.append(d)
            prt("Adding ZIP resource ", d['name'])

        elif u.resource_format == 'xlsx':
            d = dict(
                url=package_url,
                name=basename(package_url),
                format='XLSX',
                mimetype=mimetypes.guess_type(package_url)[0],
                description='Excel version of package'
            )
            resources.append(d)
            prt("Adding XLS resource ", d['name'])

        elif u.resource_format == 'csv':
            d=dict(
                url=package_url,
                name=basename(package_url),
                format='csv',
                mimetype=mimetypes.guess_type(metadata_url)[0],
                description='Package Metadata in Metatab format'
            )

            resources.append(d)
            prt("Adding {} resource {}".format(d['format'], d['name']))

            p = open_package(package_url)

            for r in p.resources():

                mimetype = mimetypes.guess_type(r.resolved_url)[0]

                try:
                    ext = mimetypes.guess_extension(mimetype)[1:]
                except:
                    ext = None

                d = dict(
                    name=r.name,
                    format = ext,
                    url=r.resolved_url,
                    mimetype=mimetype,
                    description=r.description
                )

                resources.append(d)
                prt("Adding {} resource {}".format(d['format'], d['name']))



    pkg['resources'] = resources

    c.action.package_update(**pkg)


