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
from .core import PackageBuilder
from metapack.util import ensure_dir, write_csv, slugify
from rowgenerators import Url

class FileSystemPackageBuilder(PackageBuilder):
    """Build a filesystem package"""

    def __init__(self, source_ref, package_root, cache=None, callback=None, env=None):
        super().__init__(source_ref, package_root, cache, callback, env)

        if not isdir(self.package_root):
            ensure_dir(self.package_root)

        self.package_path = join(self.package_root, self.package_name)

    def exists(self):

        return isdir(self.package_path)

    def remove(self):

        if isdir(self.package_path):
            shutil.rmtree(self.package_path)

    def is_older_than_metatada(self):
        """
        Return True if the package save file is older than the metadata. Returns False if the time of either can't be determined

        :param path: Optional extra save path, used in save_path()

        """



        try:
            return getmtime(self.save_path(path) + "/metadata.csv") > self._doc.mtime
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
        path = join(self.package_path, DEFAULT_METATAB_FILE)
        self._doc.write_csv(path)
        return path

    def _write_dpj(self):

        with open(join(self.package_path, 'datapackage.json'), 'w') as f:
            f.write(json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _write_html(self):

        with open(join(self.package_path, 'index.html'), 'w') as f:
            f.write(self._doc.html)

    def _load_resource(self, r, gen, headers):

        self.prt("Loading data for '{}' ".format(r.name))

        new_url = 'data/' + r.name + '.csv'

        path = join(self.package_path, new_url)

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)

        write_csv(path, headers, gen)

        r.url = new_url

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
            u = Url(term.value)
            if u.target_format == 'ipynb':
                notebook_docs.append(term)
                self.doc.remove_term(term)

        # Process all of the normal files
        super()._load_documentation_files()

        de = DocumentationExporter()
        fw = FilesWriter()
        fw.build_directory = join(self.package_path,'docs')

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

        path = join(self.package_path, 'docs/' + file_name)

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)

        with open(path, 'wb') as f:
            f.write(contents)

    def _load_file(self,  filename, contents):


        if "__pycache__" in filename:
            return

        path = join(self.package_path, filename)

        ensure_dir(dirname(path))

        with open(path, 'wb') as f:
            f.write(contents)