# -*- coding: utf-8 -*
# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from __future__ import print_function
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)

from IPython import get_ipython


@magics_class
class LoadMetadata(Magics):

    @cell_magic
    def metatab(self, line, cell):

        ip = get_ipython()
        ip.run_cell_magic('yaml','metatab_doc', cell)

        self.shell.user_ns.keys()

    @line_magic
    def attach_metatab(self, line):
        "my line magic"

        #print("Full access to the main IPython object:", self.shell)s
        #print("Variables in the user namespace:", list(self.shell.user_ns.keys()))

        ip = get_ipython()

        #ip.magic('config')

        shell = self.shell
        meta = shell.meta

        print(meta)

        print(self.shell.meta)

        return line

    @cell_magic
    def cmagic(self, line, cell):
        "my cell magic"
        return line, cell

    @line_cell_magic
    def lcmagic(self, line, cell=None):
        "Magic that works both as %lcmagic and as %%lcmagic"
        if cell is None:
            print("Called as line magic")
            return line
        else:
            print("Called as cell magic")
            return line, cell

