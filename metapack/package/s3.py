# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """
import json
from io import BytesIO
from os.path import join

import unicodecsv as csv

from datapackage import convert_to_datapackage
from metatab import DEFAULT_METATAB_FILE
from .core import Package
from metapack.exc import PackageError


class S3Package(Package):
    """A Zip File package"""

    def __init__(self, path=None, callback=None, cache=None, env=None, save_url=None, acl=None, force=False):

        super(S3Package, self).__init__(path, callback=callback, cache=cache, env=env)

        self._save_url = save_url

        self.bucket = None

        self.force = force

        self._acl = acl if acl else 'public-read'

    def _init_bucket(self, url=None, acl=None):

        from metapack.s3 import S3Bucket

        self._acl = acl if acl is not None else self._acl

        if not self.bucket:
            url = url or self._save_url

            self.bucket = S3Bucket(url, acl=acl)

    def save(self, url=None, acl=None):

        self.check_is_ready()

        self._init_bucket(url, acl)

        name = self.doc.find_first_value('Root.Name')

        if not name:
            raise PackageError("Package must have Root.Name term defined")

        self.prt("Preparing S3 package '{}' ".format(name))

        self.sections.resources.sort_by_term()

        self.doc.cleanse()

        self.load_declares()

        self._load_documentation_files()

        self._load_resources()

        self._clean_doc()

        self._write_doc()

        self._write_dpj()

        self._write_html()

        self.close()

        return self.access_url

    def close(self):
        pass

    @property
    def access_url(self):

        self._init_bucket()  # Fervently hope that the self.save_url has been set

        return self.bucket.access_url(self.package_name, DEFAULT_METATAB_FILE)

    @property
    def private_access_url(self):

        self._init_bucket()  # Fervently hope that the self.save_url has been set

        return self.bucket.private_access_url(self.package_name, DEFAULT_METATAB_FILE)

    @property
    def public_access_url(self):

        self._init_bucket()  # Fervently hope that the self.save_url has been set

        return self.bucket.public_access_url(self.package_name, DEFAULT_METATAB_FILE)

    @property
    def signed_url(self):
        """A URL with an access signature or password """

        self._init_bucket()  # Fervently hope that the self.save_url has been set

        return self.bucket.signed_access_url(self.package_name, DEFAULT_METATAB_FILE)

    def exists(self, url=None):

        self._init_bucket(url)

        return self.bucket.exists(self.package_name, 'index.html')

    def write_to_s3(self, path, body):

        self.bucket.write(body, join(self.package_name, path), acl=self._acl, force=self.force)

        return

    def _write_doc(self):

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerows(self.doc.rows)

        self.write_to_s3('metadata.csv', bio.getvalue())

    def _write_dpj(self):

        self.write_to_s3('datapackage.json', json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _write_html(self):
        old_ref = self._doc._ref
        self._doc._ref = self.access_url + '/metatab.csv'
        self.write_to_s3('index.html', self._doc.html)
        self._doc._ref = old_ref

    def _load_resource(self, r, gen, headers):

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