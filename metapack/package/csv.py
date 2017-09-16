# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """

from os.path import join
from metapack import PackageError
from metapack.package.core import PackageBuilder
from appurl import parse_app_url

class CsvPackageBuilder(PackageBuilder):
    """"""

    def __init__(self, source_ref=None, package_root=None,  resource_root=None, callback=None, env=None):
        super().__init__(source_ref, package_root,  callback, env)
        from metapack import MetapackPackageUrl

        self.cache_path = self.package_name + ".csv"

        self.package_path = self.package_root.join(self.cache_path)

        if self.package_root.proto == 'file':
            self.package_root.ensure_dir()

        if resource_root is not None:
            self.resource_root = resource_root
        else:
            self.resource_root = source_ref.dirname().as_type(MetapackPackageUrl)




        assert isinstance(self.resource_root, MetapackPackageUrl), (type(self.resource_root), self.resource_root)

    def _load_resource(self, source_r):
        """The CSV package has no reseources, so we just need to resolve the URLs to them. Usually, the
            CSV package is built from a file system ackage on a publically acessible server. """

        r = self.doc.resource(source_r.name)

        r.url = self.resource_root.join(r.url).inner #r.resolved_url


    def _relink_documentation(self):

        for doc in self.doc['Documentation'].find(['Root.Documentation', 'Root.Image']):
            doc.url =  doc.resolved_url

    def save(self, path=None):
        from metapack import MetapackPackageUrl
        from os.path import abspath

        # HACK ...
        if not self.doc.ref:
            self.doc._ref = self.package_path  # Really should not do this but ...

        self.check_is_ready()

        self.load_declares()

        self.doc.cleanse()

        self._load_resources()

        self._relink_documentation()

        self._clean_doc()

        if path is None:
            if self.package_path.inner.proto == 'file':
                path = self.package_path.path
            else:
                raise PackageError("Can't write doc to path: '{}'".format(path))

        self.doc.write_csv(path)

        return parse_app_url(abspath(path)).as_type(MetapackPackageUrl)