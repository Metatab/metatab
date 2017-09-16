# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """


import json
import shutil
from genericpath import exists, getmtime
from os import getcwd, makedirs, remove
from os.path import join, dirname, isdir

from nbconvert.writers import FilesWriter
from appurl import parse_app_url
from metatab.datapackage import convert_to_datapackage
from metatab import DEFAULT_METATAB_FILE
from .core import PackageBuilder
from metapack.util import ensure_dir, write_csv, slugify
from metapack.appurl import MetapackUrl


class FileSystemPackageBuilder(PackageBuilder):
    """Build a filesystem package"""

    def __init__(self, source_ref, package_root, callback=None, env=None):

        super().__init__(source_ref, package_root,  callback, env)

        if not self.package_root.isdir():
            self.package_root.ensure_dir()

        self.cache_path = join(self.package_name, DEFAULT_METATAB_FILE)

        self.package_path = self.package_root.join(self.package_name)

        self.doc_file = self.package_path.join(DEFAULT_METATAB_FILE)



    def exists(self):

        return self.package_path.isdir()

    def remove(self):

        if self.package_path.is_dir():
            shutil.rmtree(self.package_path.path)

    def is_older_than_metatada(self):
        """
        Return True if the package save file is older than the metadata. Returns False if the time of either can't be determined

        :param path: Optional extra save path, used in save_path()

        """

        try:
            path = self.doc_file.path
        except AttributeError:
            path = self.doc_file

        try:
            return getmtime(path) > self._doc.mtime

        except (FileNotFoundError, OSError):
            return False


    def save(self):

        self.check_is_ready()

        self.sections.resources.sort_by_term()

        self.doc.cleanse()

        self.load_declares()

        self._load_documentation_files()

        self._load_resources()

        self._load_files()

        self._write_dpj()

        self._clean_doc()

        doc_file = self._write_doc()

        self._write_html()

        return doc_file

    def _write_doc(self):

        self._doc.write_csv(self.doc_file)
        return MetapackUrl(self.doc_file, downloader=self._downloader)

    def _write_dpj(self):

        with open(join(self.package_path.path, 'datapackage.json'), 'w') as f:
            f.write(json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _write_html(self):

        with open(join(self.package_path.path, 'index.html'), 'w') as f:
            f.write(self._doc.html)


    def _load_resource(self, source_r):
        """The CSV package has no reseources, so we just need to resolve the URLs to them. Usually, the
            CSV package is built from a file system ackage on a publically acessible server. """

        from itertools import islice


        r = self.datafile(source_r.name)

        self.prt("Loading data for '{}' ".format(r.name))

        r.url = 'data/' + r.name + '.csv'

        path = join(self.package_path.path, r.url)

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)


        gen = islice(source_r, 1, None)
        headers = source_r.headers
        write_csv(path, headers, gen)

        # Writting between resources so row-generating programs and notebooks can
        # access previously created resources. We have to clean the doc before writing it

        ref = self._write_doc()

        # What a wreck ... we also have to get rid of the 'Transform' values, since the CSV files
        # that are written don't need them, and a lot of intermediate processsing ( specifically,
        # jupyter Notebooks, ) does not load them.
        p = FileSystemPackageBuilder(ref, self.package_root)
        p._clean_doc()
        ref = p._write_doc()

    def _load_documentation_files(self):

        from metapack.jupyter.exporters import DocumentationExporter

        notebook_docs = []

        # First find and remove them from the doc.
        for term in list(self.doc['Documentation'].find('Root.Documentation')):
            u = parse_app_url(term.value)
            if u.target_format == 'ipynb':
                notebook_docs.append(term)
                self.doc.remove_term(term)

        # Process all of the normal files
        super()._load_documentation_files()

        de = DocumentationExporter()
        fw = FilesWriter()
        fw.build_directory = join(self.package_path.path,'docs')

        # Now, generate the documents directly into the filesystem package
        for term in notebook_docs:
            u = parse_app_url(term.value)
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

        path = join(self.package_path.path, 'docs/' + file_name)

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)

        with open(path, 'wb') as f:
            f.write(contents)

    def _load_file(self,  filename, contents):


        if "__pycache__" in filename:
            return

        path = join(self.package_path.path, filename)

        ensure_dir(dirname(path))

        with open(path, 'wb') as f:
            f.write(contents)