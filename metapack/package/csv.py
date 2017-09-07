# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """

from os import getcwd
from os.path import join, dirname
from metapack.util import ensure_dir

from metapack.package.core import PackageBuilder

class CsvPackageBuilder(PackageBuilder):
    """"""

    def __init__(self, source_ref=None, package_root=None,  callback=None, env=None):
        super().__init__(source_ref, package_root,  callback, env)

        self.package_path = self.package_root.join(self.package_name + ".csv")

        try:
            self.package_root.ensure_dir()
        except AttributeError:
            # Only works for file system packages.
            pass

    def _load_resource(self, source_r):
        """The CSV package has no reseources, so we just need to resolve the URLs to them. Usually, the
            CSV package is built from a file system ackage on a publically acessible server. """

        r = self.doc.resource(source_r.name)

        from itertools import islice
        gen = islice(r, 1, None)
        headers = r.headers

        r.url = r.resolved_url

    def _relink_documentation(self):

        for doc in self.doc['Documentation'].find(['Root.Documentation', 'Root.Image']):
            doc.url =  doc.resolved_url

    def save(self, path=None):

        # HACK ...
        if not self.doc.ref:
            self.doc._ref = self.package_path  # Really should not do this but ...

        self.check_is_ready()

        self.load_declares()

        self.doc.cleanse()

        self._load_resources()

        self._relink_documentation()

        self._clean_doc()


        assert self.package_path.inner.proto == 'file', self.package_path

        self.doc.write_csv(self.package_path.path)

        return self.package_path