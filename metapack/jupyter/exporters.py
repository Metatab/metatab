# -*- coding: utf-8 -*
# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Exporter to convert a notebook into a Metatab package.
"""

import logging

import copy
import io
import metatab
import metatab.jupyter
import nbformat
from metatab.exc import MetapackError
from metatab.jupyter.markdown import MarkdownExporter
from nbconvert.exporters import Exporter
from nbconvert.exporters.html import HTMLExporter
from nbconvert.exporters.pdf import PDFExporter
from nbconvert.exporters.latex import LatexExporter
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors import ExtractOutputPreprocessor
from nbconvert.preprocessors.execute import CellExecutionError
from os import getcwd
from os.path import dirname, join, abspath
from traitlets import List
from traitlets.config import Unicode, Config, Dict
from .preprocessors import (AddEpilog, ExtractInlineMetatabDoc, RemoveMetatab,
                            ExtractFinalMetatabDoc, ExtractMetatabTerms, ExtractLibDirs)

from metatab.util import ensure_dir

def write_files(self, resources):
    self.log.info('Base dir: {}'.format(self.output_dir))

    for filename, data in resources.get('outputs', {}).items():
        dest = join(self.output_dir, filename)

        ensure_dir(dest)

        with io.open(dest, 'wb') as f:
            f.write(data)
            self.log.info("Wrote '{}' ".format(filename))

class MetatabExporter(Exporter):

    template_path = List(['.']).tag(config=True, affects_environment=True)

    output_dir = Unicode(help='Output directory').tag(config=True)
    notebook_dir = Unicode(help='CWD in which notebook will be executed').tag(config=True)
    package_dir = Unicode(help='Directory in which to store generated package').tag(config=True)
    package_name = Unicode(help='Name of package to generate. Defaults to the Metatab Root.Name').tag(config=True)


    def __init__(self, config=None, **kw):
        # import pdb; pdb.set_trace();
        super().__init__(config, **kw)

        self.log = kw.get('log', logging.getLogger(self.__class__.__name__))

    def from_file(self, file_stream, resources=None, **kw):
        return super().from_file(file_stream, resources, **kw)

    def from_filename(self, filename, resources=None, **kw):

        if not self.notebook_dir:
            self.notebook_dir = dirname(abspath(filename))

        return super().from_filename(filename, resources, **kw)



class DocumentationExporter(MetatabExporter):

    metadata = Dict(help='Extra metadata, added to the \'metatab\' key', default_value={}).tag(config=True)

    @property
    def default_config(self):
        c = Config()

        c.TemplateExporter.template_path = [dirname(metatab.jupyter.__file__)]

        c.HTMLExporter.preprocessors = [
            'metatab.jupyter.preprocessors.NoShowInput',
            'metatab.jupyter.preprocessors.RemoveMetatab',
            'metatab.jupyter.preprocessors.HtmlBib'
        ]

        c.HTMLExporter.exclude_input_prompt = True
        c.HTMLExporter.exclude_output_prompt = True

        c.MarkdownExporter.preprocessors = ['metatab.jupyter.preprocessors.RemoveMagics']

        c.PDFExporter.preprocessors = [
            'metatab.jupyter.preprocessors.NoShowInput',
            'metatab.jupyter.preprocessors.RemoveMetatab',
            'metatab.jupyter.preprocessors.LatexBib',
            'metatab.jupyter.preprocessors.MoveTitleDescription'
        ]
        c.PDFExporter.exclude_input_prompt = True
        c.PDFExporter.exclude_output_prompt = True

        c.merge(super(DocumentationExporter, self).default_config)
        return c

    def from_notebook_node(self, nb, resources=None, **kw):

        nb_copy = copy.deepcopy(nb)

        nb_copy['metadata']['metatab'] = self.metadata

        # get the Normal HTML output:
        output, resources = HTMLExporter(config=self.config).from_notebook_node(nb_copy)

        resources['unique_key'] = 'notebook'

        # Get all of the image resources
        nb_copy, resources = self.extract_resources(nb_copy, resources)

        # Add resources for the html and markdown versionf of the notebook
        self.add_pdf(nb_copy, resources)
        self.add_markdown_doc(nb_copy, resources)
        self.add_html_doc(nb_copy, resources)
        self.add_basic_html_doc(nb_copy, resources)

        return output, resources

    def extract_resources(self, nb, resources):

        output_filename_template = "image_{cell_index}_{index}{extension}"

        return ExtractOutputPreprocessor(output_filename_template=output_filename_template) \
            .preprocess(nb, resources)

    def add_pdf(self, nb, resources):
        exp = PDFExporter(config=self.config, template_file='notebook.tplx')

        (body, _) = exp.from_notebook_node(nb)

        resources['outputs']['documentation.pdf'] = body

        exp = LatexExporter(config=self.config, template_file='notebook.tplx')

        (body, _) = exp.from_notebook_node(nb)

        resources['outputs']['documentation.latex'] = body.encode('utf-8')

    def add_basic_html_doc(self, nb, resources):
        html_exp = HTMLExporter(config=self.config, template_file='hide_input_html_basic.tpl')

        (html_basic_body, _) = html_exp.from_notebook_node(nb)

        resources['outputs']['html_basic_body.html'] = html_basic_body.encode('utf-8')

    def add_html_doc(self, nb, resources):
        html_exp = HTMLExporter(config=self.config, template_file='hide_input_html.tpl')

        (html_full_body, _) = html_exp.from_notebook_node(nb)

        resources['outputs']['documentation.html'] = html_full_body.encode('utf-8')

    def add_markdown_doc(self, nb, resources):

        exp = MarkdownExporter(config=self.config)
        (md_body, _) = exp.from_notebook_node(nb)

        resources['outputs']['documentation.md'] = md_body.encode('utf-8')

    def update_metatab(self, doc, resources):
        """Add documentation entries for resources"""
        if not 'Documentation' in doc:
            doc.new_section("Documentation")

        ds = doc['Documentation']

        # This is the main output from the HTML exporter, not a resource.
        ds.new_term('Root.Documentation', 'docs/notebook.html', name="notebook.html", title='Jupyter Notebook (HTML)')

        for name, data in resources.get('outputs', {}).items():

            if name == 'documentation.html':
                ds.new_term('Root.Documentation', 'docs/' + name, title='Primary Documentation (HTML)')

            elif name == 'html_basic_body.html':
                pass
            elif name.endswith('.html'):
                ds.new_term('Root.Documentation', 'docs/' + name, title='Documentation (HTML)')
            elif name.endswith('.md'):
                ds.new_term('Root.Documentation', 'docs/'+ name, title='Documentation (Markdown)')
            elif name.endswith('.pdf'):
                ds.new_term('Root.Documentation', 'docs/'+ name, title='Documentation (PDF)')

            elif name.endswith('.png'):
                ds.new_term('Root.Image', 'docs/'+name, title='Image for HTML Documentation')


class PackageExporter(MetatabExporter):
    """

    """

    file_extension = ''

    _preprocessors = List([

    ])

    extra_terms = [] # Terms set in the document

    lib_dirs = [] # Extra library directories

    doc = None

    @property
    def default_config(self):

        c = Config()

        c.ExecutePreprocessor.timeout = 600

        c.merge(super(PackageExporter, self).default_config)
        return c

    def get_package_dir_name(self, nb):

        package_name = self.package_name

        if not package_name:
            doc = ExtractInlineMetatabDoc().run(nb)

            package_name = doc.as_version(None).find_first_value('Root.Name')

        package_dir = self.package_dir

        if not package_dir:
            package_dir = getcwd()

        return package_dir, package_name

    def get_output_dir(self,nb):
        """Open a notebook and determine the output directory from the name"""
        self.package_dir, self.package_name = self.get_package_dir_name(nb)

        return join(self.package_dir, self.package_name)

    def extract_terms(self, nb):
        """Extract some term values, usually set with tags or metadata"""
        emt = ExtractMetatabTerms()
        emt.preprocess(nb, {})

        return emt.terms

    def from_notebook_node(self, nb, resources=None, **kw):
        """Create a Metatab package from a notebook node """

        nb_copy = copy.deepcopy(nb)

        # The the package name and directory, either from the inlined Metatab doc,
        # or from the config

        self.output_dir = self.get_output_dir(nb)

        resources = self._init_resources(resources)

        resources['outputs'] = {}

        if 'language' in nb['metadata']:
            resources['language'] = nb['metadata']['language'].lower()

        # Do any other configured preprocessing
        nb_copy, resources = self._preprocess(nb_copy, resources)

        # The Notebook can set some terms with tags
        self.extra_terms = self.extract_terms(nb_copy)

        # Clear the output before executing
        self.clear_output(nb_copy)

        try:

            nb_copy, resources = self.exec_notebook(nb_copy, resources, self.notebook_dir)
        except CellExecutionError as e:

            raise CellExecutionError("Errors executing noteboook. See output at {} for details.\n{}"
                                     .format('notebooks/executed-source.ipynb', ''))

        eld = ExtractLibDirs()
        eld.preprocess(nb_copy, {})

        self.lib_dirs = eld.lib_dirs

        efm = ExtractFinalMetatabDoc()
        efm.preprocess(nb_copy, {})

        if not efm.doc:
            raise MetapackError("No metatab doc")

        self.doc = efm.doc

        for section, term, value in self.extra_terms:
            self.doc[section].get_or_new_term(term, value)

        nb, _ = RemoveMetatab().preprocess(nb, {})

        resources['outputs']['notebooks/{}.ipynb'.format(self.package_name)] = nbformat.writes(nb).encode('utf-8')

        return efm.doc.as_csv(), resources

    def clear_output(self, nb):

        from nbconvert.preprocessors import ClearOutputPreprocessor

        return ClearOutputPreprocessor().preprocess(nb, {})

    def exec_notebook(self, nb, resources, nb_dir):


        nb, _ = AddEpilog(pkg_dir=self.output_dir).preprocess(nb, resources)

        resources['outputs']['notebooks/executed-source.ipynb'] = nbformat.writes(nb).encode('utf-8')

        ep = ExecutePreprocessor(config=self.config)


        nb, _ = ep.preprocess(nb, {'metadata': {'path': nb_dir}})


        return nb, resources


