# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
NBConvert preprocessors
"""

from traitlets import Integer
from nbconvert.preprocessors import Preprocessor
from textwrap import dedent
from .magic import MetatabMagic

class RemoveMetatab(Preprocessor):
    """NBConvert preprocessor to remove the %metatab block"""

    def preprocess(self, nb, resources):
        import re

        out_cells = []

        mt_doc_name = 'mt_pkg'

        for cell in nb.cells:

            source = cell['source']

            if source.startswith('%%metatab'):

                lines = source.splitlines() # resplit to remove leading blank lines
                args = MetatabMagic.metatab_args(lines[0].replace('%%metatab',''))

                cell.source = ("import metatab as mt\n"
                               "{mt_doc_name} =  mt.ipython.open_package(locals())"
                               ).format(mt_doc_name=args['OUTVAR'])
                cell.outputs = []
            else:
                cell.source = re.sub(r'\%mt_[^\n]+\n', '', source)

            out_cells.append(cell)

        nb.cells = out_cells

        return nb, resources

class RemoveMagics(Preprocessor):
    """Remove line magic lines, or entire cell magic cells"""

    def preprocess(self, nb, resources):
        import re

        for cell in nb.cells:
            if re.match(r'^\%\%', cell.source):
                cell.source = ''
            else:
                cell.source = re.sub(r'\%[^\n]+\n', '', cell.source)

        return nb, resources

class NoShowInput(Preprocessor):
    """NBConvert preprocessor to add hide_input metatab to cells """

    def preprocess(self, nb, resources):
        import re

        out_cells = []

        for cell in nb.cells:

            #  Code cells aren't displayed at all, unless it starts with
            # a '%mt_showinput' magic, which is removed

            if cell['cell_type'] == 'code':

                source = cell['source']

                if source.startswith('%mt_showinput'):
                    cell['source'] = re.sub(r'\%mt_showinput','',source)
                else:
                    cell['metadata']['hide_input'] = True

            out_cells.append(cell)

        nb.cells = out_cells

        return nb, resources

