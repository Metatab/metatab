# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

import sys
import six
import mimetypes
from metatab import _meta, DEFAULT_METATAB_FILE, resolve_package_metadata_url, MetatabDoc, open_package
from metatab.cli.core import prt, err
from .metapack import metatab_derived_handler
from rowgenerators import get_cache, Url
from rowgenerators.util import clean_cache
from os import getenv, getcwd
from os.path import join, basename


def metakan():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metakan',
        description='CKAN management of Metatab packages, version {}'.format(_meta.__version__),
         )

    parser.add_argument('-i', '--info', default=False, action='store_true',
                   help="Show configuration information")

    parser.add_argument('-C', '--ckanurl', help="URL for CKAN instance")

    parser.add_argument('-S3', '--s3url', help="URL to S3 where packages will be stored")

    derived_group = parser.add_argument_group('Derived Packages', 'Generate other types of packages')

    derived_group.add_argument('-e', '--excel', action='store_true', default=False,
                               help='Create an excel archive from a metatab file')

    derived_group.add_argument('-z', '--zip', action='store_true', default=False,
                               help='Create a zip archive from a metatab file')

    derived_group.add_argument('-s3', '--s3', action='store_true', default=False,
                               help='Create a s3 archive from a metatab file. Argument is an S3 URL with the bucket name and '
                                    'prefix, such as "s3://devel.metatab.org/excel/". Uses boto configuration for credentials')

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

            if self.args.s3:
                self.args.s3 = self.args.s3url

            self.api_key = getenv('METAKAN_API_KEY')

            self.ckan_url = self.args.ckanurl or getenv('METAKAN_CKAN_URL')

            self.s3_url = self.args.s3url or getenv('METAKAN_S3_URL')

            if not self.ckan_url:
                err("Set the --ckanurl option or the  env var METAKAN_CKAN_URL to set the URL of a ckan instance")

            if not self.s3_url:
                err("Set the --s3url option env var METAKAN_S3_URL to set the URL to an s3 bucket")

            if not self.api_key:
                err("Set the env var METAKAN_API_KEY with the API key to a CKAN instance")

    m = MetapackCliMemo(parser.parse_args(sys.argv[1:]))

    if m.args.info:
        prt('Version  : {}'.format(_meta.__version__))
        prt('Cache dir: {}'.format(str(m.cache.getsyspath('/'))))
        exit(0)


    created = metatab_derived_handler(m, skip_if_exists=True)

    send_to_ckan(m, created)

    exit(0)

class S3Bucket(object):
    def __init__(self, url):
        from rowgenerators import parse_url_to_dict
        import boto3

        self._s3 = boto3.resource('s3')

        p = parse_url_to_dict(url)

        if p['netloc']:  # The URL didn't have the '//'
            self._prefix = p['path']
            bucket_name = p['netloc']
        else:
            proto, netpath = url.split(':')
            bucket_name, self._prefix = netpath.split('/', 1)

        self._bucket_name = bucket_name
        self._bucket = self._s3.Bucket(bucket_name)


    def access_url(self, *paths):
        import boto3

        key = join(self._prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return '{}/{}/{}'.format(s3.meta.endpoint_url.replace('https', 'http'), self._bucket_name, key)

    def write(self, body, *paths):
        from botocore.exceptions import ClientError
        import mimetypes

        if isinstance(body, six.string_types):
            with open(body,'rb') as f:
                body = f.read()

        key = join(self._prefix, *paths).strip('/')

        try:
            o = self._bucket.Object(key)
            if o.content_length == len(body):
                prt("File '{}' already in bucket; skipping".format(key))
                return self.access_url(*paths)
            else:
                prt("File '{}' already in bucket, but length is different; re-wirtting".format(key))

        except ClientError as e:
            if int(e.response['Error']['Code']) != 404:
                raise

        ct = mimetypes.guess_type(key)[0]

        try:
            self._bucket.put_object(Key=key, Body=body, ACL='public-read',
                                           ContentType=ct if ct else 'binary/octet-stream')
        except Exception as e:
            self.err("Failed to write '{}': {}".format(key, e))

        return self.access_url(*paths)


def send_to_ckan(m, created_packages):
    from ckanapi import RemoteCKAN, NotAuthorized, NotFound
    from metatab import Package

    try:
        doc = MetatabDoc(m.mt_file, cache=m.cache)
    except IOError as e:
        err("Failed to open metatab '{}': {}".format(m.mt_file, e))

    c = RemoteCKAN(m.ckan_url, apikey=m.api_key)

    s3 = S3Bucket(m.s3_url)

    identifier = doc.find_first_value('Root.Identitfier')
    name = doc.find_first('Root.Name')

    ckan_name = name.value.replace('.','-')

    try:
        pkg = c.action.package_show(name_or_id=ckan_name)
    except NotFound:
        pkg = c.action.package_create(name=ckan_name, package_id=identifier)

    pkg['title'] = doc.find_first_value('Root.Title')
    pkg['notes'] = doc.markdown #doc.find_first_value('Root.Description')
    pkg['version'] = name.properties.get('version')

    extras = []

    for t in doc.find('*.*', section='Root'):
        extras.append({'key':t.qualified_term, 'value':t.value})

    for t in name.children:
        extras.append({'key': t.qualified_term, 'value': t.value})

    pkg['extras'] = extras

    #import json
    #print(json.dumps(pkg, indent=4))

    resources = []

    for ptype, path, created in created_packages:
        print(ptype, path, created)

        if ptype == 'zip':
            url = s3.write(path, 'zip', basename(path))
            resources.append(dict(
                url=url,
                name=basename(path),
                format='ZIP',
                mimetype=mimetypes.guess_type(path)[0],
                description='ZIP version of package'
            ))

        elif ptype == 'xlsx':
            url = s3.write(path, 'zip', basename(path))
            resources.append(dict(
                url=url,
                name=basename(path),
                format='XLSX',
                mimetype=mimetypes.guess_type(path)[0],
                description='Excel version of package'
            ))

        elif ptype == 's3':
            resources.append(dict(
                name='metadata.csv',
                url=path+'/metadata.csv',
                format='csv',
                mimetype='text/csv',
                description='Package Metadata in Metatab format'
            ))

            p = open_package(path)

            for r in p.resources():

                resources.append(dict(
                    name=r.name,
                    url=r.resolved_url,
                    mimetype=mimetypes.guess_type(r.resolved_url)[0],
                    description=r.description
                ))



    pkg['resources'] = resources

    c.action.package_update(**pkg)


