# -*- coding: utf-8 -*
# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Exporter to convert a notebook into a Metatab package.
"""

from textwrap import dedent

import metatab
import metatab.jupyter
import nbformat
from metatab.cli.core import DEFAULT_METATAB_FILE
from metatab.jupyter.markdown import MarkdownExporter
from nbconvert.exporters import Exporter
from nbconvert.exporters.html import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError
from nbconvert.writers.files import FilesWriter
from nbformat.notebooknode import from_dict
from os import getcwd, makedirs
from os.path import dirname, join, abspath, exists
from traitlets import List
from traitlets.config import Bool, Unicode, Config
from .preprocessors import ( AddEpilog, RemoveMetatab, ExtractInlineMetatabDoc, RemoveMetatab,
                             ExtractFinalMetatabDoc, ExtractMetatabTerms, ExtractMaterializedRefs)
import io
import copy
import nbformat

import logging

class PackageExporter(Exporter):
    """

    """

    file_extension = ''

    notebook_dir = Unicode(help='CWD in which notebook will be executed').tag(config=True)
    package_dir = Unicode(help='Directory in which to store generated package').tag(config=True)
    package_name = Unicode(help='Name of package to generate. Defaults to the Metatab Root.Name').tag(config=True)

    output_dir = None

    _preprocessors = List([

    ])

    def __init__(self, config=None, **kw):
        #import pdb; pdb.set_trace();
        super().__init__(config, **kw)

        self.log = kw.get('log', logging.getLogger(self.__class__.__name__))

    @property
    def default_config(self):

        c = Config()

        c.ExecutePreprocessor.timeout = 600

        c.HTMLExporter.preprocessors = [
            'metatab.jupyter.preprocessors.NoShowInput',
            'metatab.jupyter.preprocessors.RemoveMetatab'
        ]

        c.HTMLExporter.preprocessors = [
                                        'metatab.jupyter.preprocessors.RemoveDocsFromImages',
                                        'metatab.jupyter.preprocessors.NoShowInput',
                                        'metatab.jupyter.preprocessors.RemoveMetatab'
                                        ]

        c.HTMLExporter.exclude_input_prompt = True
        c.HTMLExporter.exclude_output_prompt = True

        c.HTMLExporter.template_path = [dirname(metatab.jupyter.__file__)]

        c.MarkdownExporter.preprocessors = ['metatab.jupyter.preprocessors.RemoveMagics']

        c.NbConvertApp.output_files_dir = '/tmp/boo/baz'

        c.merge(super(PackageExporter, self).default_config)
        return c

    def get_package_dir_name(self, nb):

        package_name = self.package_name

        if not package_name:
            emd = ExtractInlineMetatabDoc()
            nb, _ = emd.preprocess(nb, {})

            package_name = emd.doc.as_version(None).find_first_value('Root.Name')

        package_dir = self.package_dir

        if not package_dir:
            package_dir = getcwd()

        return package_dir, package_name

    def extract_terms(self, nb):
        """Extract some term values, usually set with tags or metadata"""
        emt = ExtractMetatabTerms()
        emt.preprocess(nb, {})

        return emt.terms

    def from_file(self, file_stream, resources=None, **kw):
        return super().from_file(file_stream, resources, **kw)

    def from_filename(self, filename, resources=None, **kw):

        if not self.notebook_dir:
            self.notebook_dir = dirname(abspath(filename))

        return super().from_filename(filename, resources, **kw)

    def from_notebook_node(self, nb, resources=None, **kw):
        """Create a Metatab package from a notebook node """

        nb_copy = copy.deepcopy(nb)

        # The the package name and directory, either from the inlined Metatab doc,
        # or from the config
        self.package_dir, self.package_name = self.get_package_dir_name(nb)

        self.output_dir = join(self.package_dir, self.package_name)

        resources = self._init_resources(resources)

        if 'language' in nb['metadata']:
            resources['language'] = nb['metadata']['language'].lower()

        # Do any other configured preprocessing
        nb_copy, resources = self._preprocess(nb_copy, resources)

        # Get all of the image resources
        nb_copy, resources = self.extract_resources(nb_copy, resources)

        # Add resources for the hml and markdown versionf of the notebook
        self.add_markdown_doc(nb_copy, resources)
        self.add_html_doc(nb_copy, resources)
        self.add_basic_html_doc(nb_copy, resources)

        # The Notebook can set some terms with tags
        terms = self.extract_terms(nb_copy)

        # Clear the output before executing
        self.clear_output(nb_copy)

        try:

            nb_copy, resources = self.exec_notebook(nb_copy, resources, self.notebook_dir)



        except CellExecutionError as e:

            raise CellExecutionError("Errors executing noteboook. See output at {} for details.\n{}"
                                     .format(self.output_dir, ''))
        finally:
            self.write_files(resources)

        return nb, resources


    def clear_output(self, nb):

        from nbconvert.preprocessors import ClearOutputPreprocessor

        return ClearOutputPreprocessor().preprocess(nb, {})

    def extract_resources(self, nb, resources):

        from nbconvert.preprocessors import ExtractOutputPreprocessor

        output_filename_template = "docs/image_{cell_index}_{index}{extension}"

        return ExtractOutputPreprocessor(output_filename_template=output_filename_template)\
            .preprocess(nb, resources)

    def add_basic_html_doc(self, nb, resources):

        html_exp = HTMLExporter(config=self.config, template_file='hide_input_html_basic.tpl')

        (html_basic_body, _) = html_exp.from_notebook_node(nb)

        resources['outputs']['docs/html_basic_body.html'] = html_basic_body.encode('utf-8')

    def add_html_doc(self, nb, resources):

        html_exp = HTMLExporter(config=self.config, template_file='hide_input_html.tpl')

        (html_full_body, _) = html_exp.from_notebook_node(nb)

        resources['outputs']['docs/documentation.html'] = html_full_body.encode('utf-8')

    def add_markdown_doc(self, nb, resources):

        exp = MarkdownExporter(config=self.config)
        (md_body, _) = exp.from_notebook_node(nb)

        resources['outputs']['docs/documentation.md'] = md_body.encode('utf-8')

    def exec_notebook(self, nb, resources, nb_dir):

        nb, _ = AddEpilog(pkg_dir=self.output_dir).preprocess(nb, resources)

        resources['outputs']['notebooks/executed-source.ipynb'] = nbformat.writes(nb).encode('utf-8')

        ep = ExecutePreprocessor()

        nb, _ = ep.preprocess(nb, {'metadata': {'path': nb_dir}})

        nb, resources = self.add_metatab_doc(nb, resources)

        nb, _ = RemoveMetatab().preprocess(nb, {})

        resources['outputs']['notebooks/{}.ipynb'.format(self.package_name)] = nbformat.writes(nb).encode('utf-8')

        return nb, resources

    def add_metatab_doc(self, nb, resources):

        efm = ExtractFinalMetatabDoc()
        efm.preprocess(nb, {})

        doc = efm.doc.get_or_new_section('Documentation')

        for name, data in resources.get('outputs', {}).items():

            if name.startswith('docs/'):
                t = None
                if name.endswith('.html') or name.endswith('.md'):
                    t = doc.new_term('Root.Documentation', 'file:'+name, title='Documentation')

                elif name.endswith('.png'):
                    t = doc.new_term('Root.Image',  name, title='Image for HTML Documentation')

        resources['outputs'][DEFAULT_METATAB_FILE] = efm.doc.as_csv()

        emr = ExtractMaterializedRefs()
        emr.preprocess(nb, {})

        materialized_refs = emr.materialized

        return nb, resources


    def ensure_dir(self, path):

        if path:
            dr = dirname(path)
            if not exists(dr):

                makedirs(dr)

    def write_files(self, resources):

        self.log.info('Base dir: {}'.format(self.output_dir))

        for filename, data in resources.get('outputs', {}).items():
            dest = join(self.output_dir, filename)

            self.ensure_dir(dest)

            with io.open(dest, 'wb') as f:
                f.write(data)
                self.log.info("Wrote '{}' ".format(filename))

