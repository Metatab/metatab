# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Metapack exporter for Jupyter notebooks.
"""

from traitlets import default
from traitlets.config import Config
from nbconvert.exporters.notebook import NotebookExporter
from nbconvert.exporters.exporter import Exporter

from nbconvert.exporters.templateexporter import TemplateExporter


class MetapackExporter(TemplateExporter):
    """
    Exports to a markdown document (.md)
    """

    @default('file_extension')
    def _file_extension_default(self):
        return '.md'

    @default('template_file')
    def _template_file_default(self):
        return 'markdown'

    output_mimetype = 'text/markdown'

    @default('raw_mimetypes')
    def _raw_mimetypes_default(self):
        return ['text/markdown', 'text/html', '']

    @property
    def default_config(self):
        c = Config({
            'ExtractOutputPreprocessor': {'enabled': True},
            'NbConvertBase': {
                'display_data_priority': ['text/html',
                                          'text/markdown',
                                          'image/svg+xml',
                                          'text/latex',
                                          'image/png',
                                          'image/jpeg',
                                          'text/plain'
                                          ]
            },

        })
        c.merge(super(MarkdownExporter, self).default_config)
        return c