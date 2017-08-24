# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """

from os import getcwd
from os.path import join, dirname
from metapack.util import ensure_dir

from metapack.package.core import PackageBuilder

class CsvPackageBuilder(PackageBuilder):
    """"""

    def __init__(self, source_ref=None, package_root=None, cache=None, callback=None, env=None):
        super().__init__(source_ref, package_root, cache, callback, env)

        self.package_path = join(self.package_root, self.package_name + ".csv")

        ensure_dir(self.package_root)

    def _load_resource(self, r, gen, headers):
        """The CSV package has no reseources, so we just need to resolve the URLs to them. Usually, the
        CSV package is built from a file system ackage on a publically acessible server. """

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


        self.doc.write_csv(self.package_path)

        return self.package_path