# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """


import json
import shutil
from genericpath import exists, getmtime
from os import getcwd, makedirs, remove
from os.path import join, dirname, isdir

from nbconvert.writers import FilesWriter

from datapackage import convert_to_datapackage
from metatab import DEFAULT_METATAB_FILE
from .core import Package
from metapack.exc import PackageError
from metapack.util import ensure_exists, ensure_dir, write_csv
from rowgenerators import Url

class FileSystemPackage(Package):
    """A File System package"""

    def __init__(self, path=None, callback=None, cache=None, env=None):

        super(FileSystemPackage, self).__init__(path, callback=callback, cache=cache, env=env)
        self.package_dir = None

    def exists(self, path=None):

        if self.package_dir is None:
            self._init_dir(path)

        return exists(join(self.save_path(path), DEFAULT_METATAB_FILE))

    def is_older_than_metatada(self, path=None):
        """
        Return True if the package save file is older than the metadata. Returns False if the time of either can't be determined

        :param path: Optional extra save path, used in save_path()

        """



        try:
            return getmtime(self.save_path(path) + "/metadata.csv") > self._doc.mtime
        except (FileNotFoundError, OSError):
            return False

    def save_path(self, path=None):

        base = self.doc.find_first_value('Root.Name')

        if path and not path.endswith('.zip'):
            return join(path, base)
        else:
            return base

    def save(self, path=None):

        self.check_is_ready()

        if not self.doc.find_first_value('Root.Name'):
            raise PackageError("Package must have Root.Name term defined")

        self.sections.resources.sort_by_term()

        self.doc.cleanse()

        self.load_declares()

        self._init_dir(path)

        ensure_exists(dirname(self.save_path(path)))

        self._load_documentation_files()

        self._load_resources()

        self._load_files()

        self._write_dpj()

        self._clean_doc()

        doc_file = self._write_doc()

        self._write_html()

        return doc_file

    def remove(self, path=None):

        if path is None:
            path = getcwd()

        name = self.doc.find_first_value('Root.Name')

        np = join(path, name)

        if isdir(np):
            shutil.rmtree(np)

    def _init_dir(self, path=None):

        if path is None:
            path = getcwd()

        name = self.doc.find_first_value('Root.Name')

        assert path
        assert name

        np = join(path, name)

        if not isdir(np):
            makedirs(np)

        self.package_dir = np

    def _write_doc(self):
        path = join(self.package_dir, DEFAULT_METATAB_FILE)
        self._doc.write_csv(path)
        return path

    def _write_dpj(self):

        with open(join(self.package_dir, 'datapackage.json'), 'w') as f:
            f.write(json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _write_html(self):

        with open(join(self.package_dir, 'index.html'), 'w') as f:
            f.write(self._doc.html)

    def _load_resource(self, r, gen, headers):

        self.prt("Loading data for '{}' ".format(r.name))

        r.url = 'data/' + r.name + '.csv'

        path = join(self.package_dir, r.url)

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)

        write_csv(path, headers, gen)

        # Writting between resources so row-generating programs and notebooks can
        # access previously created resources. We have to clean the doc before writing it

        ref = self._write_doc()

        # What a wreck ... we also have to get rid of the 'Transform' values, since the CSV files
        # that are written don't need them, and a lot of intermediate processsing ( specifically,
        # jupyter Notebooks, ) does not load them.
        p = FileSystemPackage(ref)
        p._init_dir('_packages')
        p._clean_doc()
        ref = p._write_doc()

    def _load_documentation_files(self):

        from metapack.jupyter.exporters import DocumentationExporter

        notebook_docs = []

        # First find and remove them from the doc.
        for term in list(self.doc['Documentation'].find('Root.Documentation')):
            u = Url(term.value)
            if u.target_format == 'ipynb':
                notebook_docs.append(term)
                self.doc.remove_term(term)

        # Process all of the normal files
        super()._load_documentation_files()

        de = DocumentationExporter()
        fw = FilesWriter()
        fw.build_directory = join(self.package_dir,'docs')

        # Now, generate the documents directly into the filesystem package
        for term in notebook_docs:
            u = Url(term.value)
            nb_path = u.path(self.source_dir)

            output, resources = de.from_filename(nb_path)
            fw.write(output, resources, notebook_name='notebook')

            de.update_metatab(self.doc, resources)

    def _load_documentation(self, term, contents, file_name):

        try:
            title = term['title'].value
        except KeyError:
            self.warn("Documentation has no title, skipping: '{}' ".format(term.value))
            return

        self.prt("Loading documentation for '{}', '{}' ".format(title, file_name))

        path = join(self.package_dir, 'docs/' + file_name)

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)

        with open(path, 'wb') as f:
            f.write(contents)

    def _load_file(self,  filename, contents):


        if "__pycache__" in filename:
            return

        path = join(self.package_dir, filename)

        ensure_dir(dirname(path))

        with open(path, 'wb') as f:
            f.write(contents)