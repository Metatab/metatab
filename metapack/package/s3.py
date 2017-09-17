# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """
import json
from io import BytesIO
from os.path import join, getsize
from os import walk
import boto3
import unicodecsv as csv

from appurl import parse_app_url
from metatab import DEFAULT_METATAB_FILE

from .core import PackageBuilder




class S3PackageBuilder(PackageBuilder):
    """A Zip File package"""

    def __init__(self, source_ref=None, package_root=None, callback=None, env=None, acl=None, force=False):

        super().__init__(source_ref, package_root, callback, env)

        self.package_path = self.package_root.join(self.package_name)

        self.cache_path = self.package_name

        self.force = force

        self._acl = acl if acl else 'public-read'

        self.bucket = S3Bucket(self.package_path, acl=self._acl)

    @property
    def access_url(self):
        from metapack import MetapackPackageUrl
        return MetapackPackageUrl(self.bucket.access_url(DEFAULT_METATAB_FILE),
                                  downloader=self._source_ref.downloader)


    @property
    def private_access_url(self):
        from metapack import MetapackPackageUrl
        return MetapackPackageUrl(self.bucket.access_url(DEFAULT_METATAB_FILE),
                                  downloader=self._source_ref.downloader)

    @property
    def public_access_url(self):
        from metapack import MetapackPackageUrl

        return MetapackPackageUrl(self.bucket.public_access_url(DEFAULT_METATAB_FILE),
                                  downloader=self._source_ref.downloader)

    @property
    def signed_url(self):
        """A URL with an access signature or password """
        return self.bucket.signed_access_url(DEFAULT_METATAB_FILE)

    def exists(self, url=None):
        return self.bucket.exists(DEFAULT_METATAB_FILE)


    def save(self, url=None, acl=None):

        self.check_is_ready()

        # Resets the ref so that resource.resolved_url link to the resources as written in S3
        self._doc._ref = self.access_url.join('metatab.csv')

        self.prt("Preparing S3 package '{}' ".format(self.package_name))

        # Copy all of the files from the Filesystem package
        for root, dirs, files in walk(self.source_dir):
            for f in files:
                source = join(root, f)
                rel = source.replace(self.source_dir, '').strip('/')

                with open(source,'rb') as f:
                    self.write_to_s3(rel,f)

        # Re-write the URLS for the datafiles
        for r in self.datafiles:
            r.url = self.bucket.access_url(r.url)

        # Rewrite Documentation urls:
        for r in self.doc.find(['Root.Documentation', 'Root.Image']):
            if parse_app_url(r.url).proto == 'file':
                r.url = self.bucket.access_url(r.url)

        # re-write the metatab with the new URLs
        self._write_doc()

        # Re-write the HTML index file.
        self._write_html()

        return self.access_url

    def close(self):
        pass



    def write_to_s3(self, path, body):

        self.bucket.write(body, path, acl=self._acl, force=self.force)

        return

    def _write_doc(self):

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerows(self.doc.rows)

        self.write_to_s3('metadata.csv', bio.getvalue())

    def _write_html(self):
        old_ref = self._doc._ref
        self._doc._ref = self.access_url.join('metatab.csv')
        self.write_to_s3('index.html', self._doc.html)
        self._doc._ref = old_ref

    def _load_resource(self, r):
        from itertools import islice
        gen = islice(r, 1, None)
        headers = r.headers

        r.url = 'data/' + r.name + '.csv'

        bio = BytesIO()

        data = write_csv(bio, headers, gen)

        self.prt("Loading data ({} bytes) to '{}' ".format(len(data), r.url))

        self.write_to_s3(r.url, data)

    def _load_documentation(self, term, contents, file_name):

        title = term['title'].value

        self.prt("Loading documentation for '{}', '{}' ".format(title, file_name))

        term['url'].value = 'docs/' + file_name

        self.write_to_s3(term['url'].value, contents)


def set_s3_profile(profile_name):
    """Load the credentials for an s3 profile into environmental variables"""
    import os

    session = boto3.Session(profile_name=profile_name)

    os.environ['AWS_ACCESS_KEY_ID'] = session.get_credentials().access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = session.get_credentials().secret_key


class S3Bucket(object):

    def __init__(self, url, acl='public', profile=None):


        if url.scheme != 's3':
            raise ReferenceError("Must be an S3 url; got: {}".format(url))

        self.url = url

        session = boto3.Session(profile_name=profile)

        self._s3 = session.resource('s3')

        if acl == 'public':
            acl = 'public-read'

        self._acl = acl

        self._bucket = self._s3.Bucket(self.bucket_name)

    @property
    def prefix(self):
        return self.url.path

    @property
    def bucket_name(self):
        return self.url.netloc

    def access_url(self, *paths):

        if self._acl == 'private':
            return self.private_access_url(*paths)
        else:
            return self.public_access_url(*paths)

    def private_access_url(self, *paths):

        key = join(self.prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return "s3://{}/{}".format(self.bucket_name, key)

    def public_access_url(self, *paths):

        key = join(self.prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return '{}/{}/{}'.format(s3.meta.endpoint_url.replace('https', 'http')\
                                 .replace('/s3.amazonaws.com',''), # Assume bucket has a CNAME
                                 self.bucket_name, key)

    def signed_access_url(self, *paths):

        import pdb;
        pdb.set_trace()

        key = join(self.prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return s3.generate_presigned_url('get_object', Params={'Bucket': self.bucket_name, 'Key': key})


    def exists(self, *paths):
        import botocore

        # index.html is the last file written
        key = join(self.prefix, *paths).strip('/')

        exists = False

        try:
            self._bucket.Object(key).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                exists = False
            else:
                raise
        else:
            exists = True

        return exists

    def list(self):

        s3 = boto3.client('s3')

        # Create a reusable Paginator
        paginator = s3.get_paginator('list_objects')

        # Create a PageIterator from the Paginator
        page_iterator = paginator.paginate(Bucket=self.bucket_name)

        for page in page_iterator:
            for c in page['Contents']:
                yield c

    def write(self, body, path, acl=None, force=False):
        from botocore.exceptions import ClientError
        import mimetypes
        from metapack.cli.core import err, prt

        acl = acl if acl is not None else self._acl

        key = join(self.prefix, path).strip('/')

        try:
            file_size = getsize(body.name) # Maybe it's an open file
        except AttributeError:
            # Nope, hope it is the file contents
            file_size = len(body)

        try:
            o = self._bucket.Object(key)
            if o.content_length == file_size:
                if force:
                    prt("File '{}' already in bucket, but forcing overwrite".format(key))
                else:
                    prt("File '{}' already in bucket; skipping".format(key))
                    return self.access_url(path)
            else:
                prt("File '{}' already in bucket, but length is different; re-wirtting".format(key))

        except ClientError as e:
            if int(e.response['Error']['Code']) in (403, 405):
                err("S3 Access failed for '{}:{}': {}\nNOTE: With Docker, this error is often the result of container clock drift. Check your container clock. "
                    .format(self.bucket_name, key, e))
            elif int(e.response['Error']['Code']) != 404:
                err("S3 Access failed for '{}:{}': {}".format(self.bucket_name, key, e))

        ct = mimetypes.guess_type(key)[0]

        try:
            self._bucket.put_object(Key=key,
                                    Body=body,
                                    ACL=acl,
                                    ContentType=ct if ct else 'binary/octet-stream')
        except Exception as e:
            err("Failed to write '{}' to '{}': {}".format(key, self.bucket_name, e))

        return self.access_url(path)