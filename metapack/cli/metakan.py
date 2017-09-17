# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

import mimetypes
import traceback
from os import getenv
from os.path import join, basename

from metapack import MetapackDoc, Downloader, open_package
from metapack.cli.core import err
from metatab import _meta, DEFAULT_METATAB_FILE, MetatabError
from .core import MetapackCliMemo as _MetapackCliMemo
from .core import prt, warn, write_doc, update_dist

downloader = Downloader()

class MetapackCliMemo(_MetapackCliMemo):

    def __init__(self, args, downloader):
        super().__init__(args, downloader)

        self.api_key = self.args.api or getenv('METAKAN_API_KEY')

        self.ckan_url = self.args.ckan or getenv('METAKAN_CKAN_URL')

    def set_mt_arg(self, metatabfile):


        if not self.ckan_url:
            err("Set the --ckan option or the METAKAN_CKAN_URL env var to set the URL of a ckan instance")

        if not self.api_key:
            err("Set the --api option METAKAN_API_KEY env var  with the API key to a CKAN instance")

    def update_mt_arg(self, metatabfile):
        """Return a new memo with a new metatabfile argument"""
        o = MetapackCliMemo(self.args)
        o.set_mt_arg(metatabfile)
        return o

def metakan(subparsers):


    parser = subparsers.add_parser(
        'ckan',
        help='CKAN management of Metatab packages, version {}'.format(_meta.__version__)
    )

    parser.set_defaults(run_command=run_ckan)

    parser.add_argument('-i', '--info', default=False, action='store_true',
                   help="Show configuration information")

    parser.add_argument('-c', '--ckan', help="URL for CKAN instance")

    parser.add_argument('-a', '--api', help="CKAN API Key")

    parser.add_argument('-p', '--packages', action='store_true',
                        help="The file argument is a text file with a list of package URLs to load")

    parser.add_argument('-C', '--configure', action='store_true',
                        help="File is a CKAN configuration file in Metatab format")

    parser.add_argument('metatabfile', nargs='?', default=DEFAULT_METATAB_FILE,
                        help='Path to a Metatab file, or an s3 link to a bucket with Metatab files. ')


def run_ckan(args):

    m = MetapackCliMemo(args, downloader=downloader)

    if m.mtfile_url.scheme == 's3':
        """Find all of the top level CSV files in a bucket and use them to create CKan entries"""

        from metatab.s3 import S3Bucket

        b = S3Bucket(m.mtfile_arg)

        for e in b.list():
            key = e['Key']
            if '/' not in key and key.endswith('.csv'):
                url = b.access_url(key)
                prt("Processing", url)
                send_to_ckan(m.update_mt_arg(url))

    elif m.args.packages:

        with open(m.mtfile_arg) as f:
            for line in f.readlines():
                url = line.strip()
                prt("Processing", url)
                try:
                    send_to_ckan(m.update_mt_arg(url))
                except Exception as e:
                    warn("Failed to process {}: {}".format(line, e))


    elif m.args.configure:
        configure_ckan(m)

    else:
        send_to_ckan(m)

    exit(0)

def send_to_ckan(m):

    from ckanapi import RemoteCKAN, NotFound
    try:
        doc = MetapackDoc(m.mt_file, cache=m.cache)
    except (IOError, MetatabError) as e:
        err("Failed to open metatab '{}': {}".format(m.mt_file, e))

    c = RemoteCKAN(m.ckan_url, apikey=m.api_key)

    ckanid = doc.find_first_value('Root.Ckanid')

    unversioned_name = doc.as_version(None)
    ckan_name = unversioned_name.replace('.','-')

    id_name = ckanid or ckan_name

    try:
        pkg = c.action.package_show(name_or_id=id_name)
        prt("Updating CKAN dataset for '{}'".format(id_name))
        found = True
    except NotFound as e:
        e.__traceback__ = None
        traceback.clear_frames(e.__traceback__)
        found = False

    if not found:
        try:
            pkg = c.action.package_show(name_or_id=ckan_name)
            prt("Updating CKAN dataset for '{}'".format(id_name))
            found = True
        except NotFound as e:
            e.__traceback__ = None
            traceback.clear_frames(e.__traceback__)
            found = False

    if not found:
        try:
            pkg = c.action.package_create(name=ckan_name)
        except Exception as e:
            err("Failed to create package for name '{}': {} ".format(ckan_name, e))

        prt("Adding CKAN dataset for '{}'".format(ckan_name))

    pkg['title'] = doc.find_first_value('Root.Title')

    if not pkg['title']:
        pkg['title'] = doc.find_first_value('Root.Description')

    pkg['version'] =  doc.find_first_value('Root.Version')

    pkg['groups'] = [ {'name': g.value } for g in doc['Root'].find('Root.Group')]

    pkg['tags'] = [{'name': g.value} for g in doc['Root'].find('Root.Tag')]

    org_name = doc.get_value('Root.Origin', doc.get_value('Root.CkanOrg'))

    if org_name:
        org_name_slug = org_name.replace('.','-')
        try:

            owner_org = c.action.organization_show(id=org_name_slug).get('id')
            pkg['owner_org'] = owner_org
        except NotFound:
            warn("Didn't find org for '{}'; not setting organization ".format(org_name_slug))
            org_name_slug = None
    else:
        org_name_slug = None

    extras = {}

    for t in doc.find('*.*', section='Root'):
        if not t.term_is('Root.Distribution'):
            extras[t.qualified_term] = t.value

    pkg['extras'] = [ {'key':k, 'value':v} for k, v in extras.items() ]

    resources = []

    # Try to set the markdown from a CSV package, since it will have the
    # correct links.
    markdown = None

    for dist in doc.find('Root.Distribution'):

        prt("Processing {} package: {}".format(dist.type, dist.value))

        package_url = dist.package_url
        metadata_url = dist.metadata_url

        if dist.type == 'zip':
            d = dict(
                url=str(package_url.inner),
                name=basename(package_url.path),
                format='ZIP',
                mimetype=mimetypes.guess_type(package_url.path)[0],
                description='ZIP version of package'
            )
            resources.append(d)
            prt("Adding ZIP package ", d['name'])

        elif dist.type == 'xlsx':
            d = dict(
                url=str(package_url.inner),
                name=basename(package_url.path),
                format='XLSX',
                mimetype=mimetypes.guess_type(package_url.path)[0],
                description='Excel version of package'
            )
            resources.append(d)
            prt("Adding XLS package ", d['name'])

        elif dist.type == 'csv':

            d=dict(
                url=str(package_url.inner),
                name=basename(package_url.path),
                format='csv',
                mimetype=mimetypes.guess_type(metadata_url.path)[0],
                description='CSV Package Metadata in Metatab format'
            )

            resources.append(d)
            prt("Adding {} package {}".format(d['format'], d['name']))

            try:
                p = open_package(metadata_url)
            except (IOError, MetatabError) as e:
                err("Failed to open package '{}' from reference '{}': {}".format(package_url, dist.url, e))

            for r in p.resources():

                mimetype = mimetypes.guess_type(r.resolved_url.path)[0]

                try:
                    ext = mimetypes.guess_extension(mimetype)[1:]
                except:
                    ext = None

                d = dict(
                    name=r.name,
                    format = ext,
                    url=str(r.resolved_url),
                    mimetype=mimetype,
                    description=r.markdown
                )

                resources.append(d)
                prt("Adding {} resource {}".format(d['format'], d['name']))

        elif dist.type == 'fs':
            # Fervently hope that this is a web acessible fs distribution
            from requests import HTTPError
            from appurl import DownloadError
            try:
                doc = metadata_url.doc
                markdown = doc.markdown
            except (HTTPError, DownloadError):
                pass

        else:
            warn("Unknown distribution type '{}' for '{}'  ".format(dist.type, dist.value))


    try:
        pkg['notes'] = markdown or doc.markdown #doc.find_first_value('Root.Description')
    except (OSError, DownloadError) as e:
        warn(e)

    pkg['resources'] = resources

    c.action.package_update(**pkg)

    pkg = c.action.package_show(name_or_id=pkg['id'])

    update_dist(doc, [], join(m.ckan_url, 'dataset',ckan_name))

    ##
    ## Add a term with CKAN info.

    doc['Root'].get_or_new_term('CkanId', pkg['id'])

    if org_name_slug is None and pkg.get('organization'):
        doc['Root'].get_or_new_term('CkanOrg', (pkg.get('organization') or {}).get('name'))

    groups = doc['Root'].find('Group')
    for g in groups:
        doc.remove_term(g)

    for group in pkg.get('groups', []):
        doc['Root'].new_term('Group', group['name'])

    write_doc(doc, m.mt_file)


def configure_ckan(m):
    """Load groups and organizations, from a file in Metatab format"""
    from ckanapi import RemoteCKAN
    try:
        doc = MetapackDoc(m.mt_file, cache=m.cache)
    except (IOError, MetatabError) as e:
        err("Failed to open metatab '{}': {}".format(m.mt_file, e))

    c = RemoteCKAN(m.ckan_url, apikey=m.api_key)

    groups = { g['name']:g for g in c.action.group_list(all_fields=True) }

    for g in doc['Groups']:

        if g.value not in groups:
            prt('Creating group: ', g.value)
            c.action.group_create(name=g.value,
                                  title=g.get_value('title'),
                                  description=g.get_value('description'),
                                  id=g.get_value('id'),
                                  image_url=g.get_value('image_url'))

    orgs = {o['name']: o for o in c.action.organization_list(all_fields=True)}

    for o in doc['Organizations']:

        if o.value not in orgs:
            prt('Creating organization: ', o.value)
            c.action.organization_create(name=o.value,
                                  title=o.get_value('title'),
                                  description=o.get_value('description'),
                                  id=o.get_value('id'),
                                  image_url=o.get_value('image_url'))