# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""
import boto3
import six
from metatab.cli.core import prt, err
from os.path import join
from rowgenerators import parse_url_to_dict

def set_s3_profile(profile_name):
    """Load the credentials for an s3 profile into environmental variables"""
    import os

    session = boto3.Session(profile_name=profile_name)

    os.environ['AWS_ACCESS_KEY_ID'] = session.get_credentials().access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = session.get_credentials().secret_key

class S3Bucket(object):

    def __init__(self, url, acl='public', profile=None):

        session = boto3.Session(profile_name=profile)

        self._s3 = session.resource('s3')

        if acl == 'public':
            acl = 'public-read'

        self._acl = acl

        p = parse_url_to_dict(url)

        if p['netloc']:  # The URL didn't have the '//'
            self._prefix = p['path']
            bucket_name = p['netloc']

            if p['scheme'] != 's3':
                raise ReferenceError("Must be an S3 url; got: {}".format(url))

        else:
            try:
                proto, netpath = url.split(':')
            except ValueError:
                # Assume it's just the bucket name
                proto = 's3'
                netpath = url

            if proto != 's3':
                raise ReferenceError("Must be an S3 url; got: {}".format(url))

            try:
                bucket_name, self._prefix = netpath.split('/', 1)
            except ValueError:
                bucket_name, self._prefix = netpath, ''


        self._bucket_name = bucket_name
        self._bucket = self._s3.Bucket(bucket_name)

    @property
    def prefix(self):
        return self._prefix

    @property
    def bucket_name(self):
        return self._bucket_name

    def access_url(self, *paths):

        if self._acl == 'private':
            return self.private_access_url(*paths)
        else:
            return self.public_access_url(*paths)

    def private_access_url(self, *paths):

        key = join(self._prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return "s3://{}/{}".format(self._bucket_name, key)

    def public_access_url(self, *paths):

        key = join(self._prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return '{}/{}/{}'.format(s3.meta.endpoint_url.replace('https', 'http'), self._bucket_name, key)

    def signed_access_url(self, *paths):

        import pdb;
        pdb.set_trace()

        key = join(self._prefix, *paths).strip('/')

        s3 = boto3.client('s3')

        return s3.generate_presigned_url('get_object', Params={'Bucket': self._bucket_name, 'Key': key})


    def exists(self, *paths):
        import botocore

        # index.html is the last file written
        key = join(self._prefix, *paths).strip('/')

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
        page_iterator = paginator.paginate(Bucket=self._bucket_name)

        for page in page_iterator:
            for c in page['Contents']:
                yield c

    def write(self, body, path, acl=None, force=False):
        from botocore.exceptions import ClientError
        import mimetypes

        acl = acl if acl is not None else self._acl

        #if isinstance(body, six.string_types):
        #    with open(body,'rb') as f:
        #        body = f.read()

        key = join(self._prefix, path).strip('/')

        try:
            o = self._bucket.Object(key)
            if o.content_length == len(body):
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
                    .format(self._bucket_name, key, e))
            elif int(e.response['Error']['Code']) != 404:
                err("S3 Access failed for '{}:{}': {}".format(self._bucket_name, key, e))

        ct = mimetypes.guess_type(key)[0]

        try:
            self._bucket.put_object(Key=key,
                                    Body=body,
                                    ACL=acl,
                                    ContentType=ct if ct else 'binary/octet-stream')
        except Exception as e:
            self.err("Failed to write '{}': {}".format(key, e))

        return self.access_url(path)

