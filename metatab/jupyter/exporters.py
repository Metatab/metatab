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
from .preprocessors import ( AddEpilog, RemoveMetatab, ExtractInlineMetatabDoc,
                             ExtractFinalMetatabDoc, ExtractMetatabTerms )
import io
import copy

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

        c.HTMLExporter.preprocessors = ['nbconvert.preprocessors.ExtractOutputPreprocessor',
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

        nb_copy = copy.deepcopy(nb)

        # The the package name and directory, either from the inlined Metatab doc,
        # or from the config
        package_dir, package_name = self.get_package_dir_name(nb)

        self.output_dir = join(package_dir, package_name)

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
        self.clear_output(nb)

        # Save the notebook we're about to exec, in the form it will be executed
        nb, resources = self.add_exec_notebook(nb_copy, resources)

        nb_final, resources = self.exec_notebook(nb, resources, self.notebook_dir)

        self.write_files(resources)

        return str(nb_final), resources



    def doc_refs(self, resources):

        doc_refs = [{
            'term': 'Root.Documentation',
            'ref': 'file:docs/documentation.html',
            'name': 'documentation',
            'title': "Main documentation"
        }]

        for filename, data in resources.get('outputs', {}).items():
            doc_refs.append(
                {
                    'term': 'Root.Image',
                    'ref': 'file:docs/{}'.format(filename),
                    'name': filename,
                    'title': "Documentation image"
                }
            )

        return doc_refs

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

    def add_exec_notebook(self, nb, resources):

        nb, _ = AddEpilog().preprocess(nb, resources)

        resources['outputs']['notebooks/executed-source.ipynb'] = str(nb).encode('utf-8')

        return nb, resources

    def exec_notebook(self, nb, resources,  nb_dir):

        ep = ExecutePreprocessor()

        nb, _ = ep.preprocess(nb, {'metadata': {'path': nb_dir}})

        efm = ExtractFinalMetatabDoc()
        efm.preprocess(nb, {})

        resources['outputs'][DEFAULT_METATAB_FILE] = efm.doc.as_csv()

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


    def write_notebook(nb, nb_dir, pkg_dir, pkg_name, doc_refs=[]):
        """Executes the notebook, exports the Metatab data in it, and writes the notebook into the package.

        Also writes the metatab file that defined in the Notebook"""

        out_path = join(pkg_dir, 'notebooks', pkg_name + '.ipynb')

        try:
            # Save the notebook, before it gets pre-processed
            with open(out_path.replace('.ipynb', '-exec.ipynb'), mode='wt') as f:
                nbformat.write(nb, f)




        except CellExecutionError as e:

            raise CellExecutionError("Errors executing noteboook. See output at {} for details.\n{}"
                                     .format(out_path, ''))
        finally:
            with open(out_path, mode='wt') as f:
                nbformat.write(nb, f)

        return join(pkg_dir, DEFAULT_METATAB_FILE)

    def preprocess_notebook(m):
        import nbformat
        from metatab.jupyter.convert import write_documentation, write_notebook, get_package_dir

        if m.mtfile_url.target_format == 'ipynb':
            prt('Convert notebook to Metatab source package')
            nb_path = Url(m.mt_file).parts.path
            pkg_dir, pkg_name = get_package_dir(nb_path)

            with open(nb_path) as f:
                nb = nbformat.reads(f.read(), as_version=4)

            doc_refs = write_documentation(nb, join(pkg_dir, 'docs'))

            doc_path = write_notebook(nb, dirname(nb_path), pkg_dir, pkg_name, doc_refs)

            add_doc_refs(doc_path, doc_refs)

            # Reset the input to use the new data
            prt('Running with new package file: {}'.format(doc_path))
            m.init_stage2(doc_path, '')
