# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """

from os import getcwd
from os.path import join, dirname

from metapack.package.core import Package
from metapack.util import ensure_exists


class CsvPackage(Package):
    """"""

    def save_path(self, path=None):
        base = self.doc.find_first_value('Root.Name') + '.csv'

        if path is None:
            path = getcwd()

        if path and not path.endswith('.csv'):
            return join(path, base)
        elif path:
            return path
        else:
            return base

    def _load_resource(self, r, gen, headers):

        r.url = r.resolved_url


    def _relink_documentation(self):

        for doc in self.doc.resources(term=['Root.Documentation', 'Root.Image'], section='Documentation'):
            doc.url =  doc.resolved_url

    def save(self, path=None):

        # HACK ...
        if not self.doc.ref:
            self.doc._ref = self.save_path(path)  # Really should not do this but ...

        self.check_is_ready()

        self.load_declares()

        self.doc.cleanse()

        self._load_resources()

        self._relink_documentation()

        self._clean_doc()

        _path = self.save_path(path)

        ensure_exists(dirname(_path))

        self.doc.write_csv(_path)

        return _path