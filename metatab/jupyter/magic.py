# -*- coding: utf-8 -*
# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

jupyter nbextension install --py metatab.jupyter.magic

"""

from __future__ import print_function

import logging
import shlex

import docopt

from IPython import get_ipython
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic)
from collections import OrderedDict
from metatab import MetatabDoc
from metatab.cli.core import process_schemas
from metatab.generate import TextRowGenerator
from os import makedirs
from os.path import join, abspath, dirname
from warnings import warn


logger = logging.getLogger('user')
logger_err = logging.getLogger('cli-errors')
doc_logger = logging.getLogger('doc')
debug_logger = logging.getLogger('debug_logger')

@magics_class
class MetatabMagic(Magics):

    @staticmethod
    def metatab_args(line):
        # Using docopt b/c I didn't know about @magic_arguments
        args =  docopt.docopt(MetatabMagic.metatab.__doc__, argv=shlex.split(line))

        if not args.get('OUTVAR'):
            args['OUTVAR'] = 'mt_pkg'

        return args

    @cell_magic
    def metatab(self, line, cell):
        """Process a cell of Metatab data, in line format

        Usage: metatab [-s | --show] [OUTVAR]

        Options:
            -h --help           Show this screen.
            -s --show         Display the Metatab terms, showing any updates


        """


        ip = get_ipython()

        doc = MetatabDoc(TextRowGenerator(cell))

        doc['Root'].get_or_new_term('Root.Name')

        doc.update_name(force=True)

        if not 'Resources' in doc:
            doc.new_section('Resources', ['Name', 'Description'])
        else:
            doc['Resources'].args = \
                list(OrderedDict( (c.record_term.title(),None) for t in doc['Resources'].terms for c in t.children).keys())

        if not 'References' in doc:
            doc.new_section('References', ['Name', 'Description'])

        process_schemas(doc)

        try:
            args = self.metatab_args(line)
        except docopt.DocoptExit as e:
            warn(str(e))
        except SystemExit:
            return

        doc_var_name = args['OUTVAR']

        if not '_mt_doc_names' in self.shell.user_ns:
            self.shell.user_ns['_mt_doc_names'] = set()

            self.shell.user_ns['_mt_doc_names'].add(doc_var_name)

        self.shell.user_ns[doc_var_name] = doc

        if args['--show']:
            for l in doc.lines:
                print(': '.join(str(e) for e in l))

        logger.info("Metatab document set in variable named '{}'".format(doc_var_name))

    @line_magic
    def mt_process_schemas(self, line):
        """Add Schema entries for resources to the metatab file.

        Runs on every metatab file declared in the notebook. Does not write the doc file"""

        for doc_var_name in self.shell.user_ns['_mt_doc_names']:
            doc = self.shell.user_ns[doc_var_name]
            process_schemas(doc)


    @line_magic
    def mt_write_metatab(self, line):
        """Write a metatab files to a file.

        If --doc is not specified, writes all of the files declared in the document

        Usage: mt_write_metatab [options] [<path>]

        Options:
            path                        File name to write to. If end with '/', a path name
            -h, --help                  Show this screen.
            -D <doc>, --doc <doc>       Variable name of the metatab doc [default: mt_pkg]

        """

        try:
            args = docopt.docopt(self.mt_write_metatab.__doc__, argv=shlex.split(line))
        except docopt.DocoptExit as e:
            warn(str(e))
        except SystemExit:
            return

        debug_logger.info("Enter mt_write_metatab")

        if args['<path>']:
            if args['<path>'].endswith('/'):
                dir_name = args['<path>']
                file_name = None
            else:
                dir_name = None
                file_name = args['<path>']
        else:
            dir_name = ''
            file_name = None

        for n in self.shell.user_ns.get('_mt_doc_names'):

            doc = self.shell.user_ns[n]

            doc.update_name()

            if not dir_name:
                source_name = doc['Root'].get_value('Root.Name')

                path = abspath(join(source_name, file_name or 'metadata.csv'))
            else:
                path = abspath(join(dir_name, file_name or 'metadata.csv'))

            makedirs(dirname(path), exist_ok=True)

            path = self.shell.user_ns[n].write_csv(path)

            debug_logger.info("Wrote", n, " to ", path)


    @line_magic
    def mt_showinput(self, line):
        """Marks the cell as an input that should be shown. """


    @line_magic
    def mt_add_dataframe(self, line):
        """Add a dataframe to a metatab document's data files

        Usage: mt_add_dataframe [options] <dataframe_name>

        Options:
            dataframe_name    Variable name of the dataframe
            -h, --help         Show this screen.
            -D <doc>, --doc <doc>            Variable name of the metatab doc [default: mt_pkg]
            -t <title>, --title <title>      Title of the dataframe
            -n <name>, --name  <name>        Metadata reference name of the dataframe


        """
        from .convert import process_schema

        try:
            args = docopt.docopt(self.mt_add_dataframe.__doc__, argv=shlex.split(line))
        except docopt.DocoptExit as e:
            warn(str(e))
        except SystemExit:
            return

        doc = self.shell.user_ns[args['--doc']]

        notebook_name = doc['Root'].get_value('name','notebook')

        df = self.shell.user_ns[args['<dataframe_name>']]

        name = args['--name'] or df.name
        title = args['--title'] or df.title or df.desc

        ref='ipynb:notebooks/{}.ipynb#{}'.format(notebook_name,  args['<dataframe_name>'])

        if not 'Resources' in doc:
            doc.new_section('Resources')

        t = doc['Resources'].get_or_new_term("Root.Datafile", ref)

        t['name'] = name
        t['title'] = title

        process_schema(doc,doc.resource(name), df)

    @line_magic
    def mt_notebook_path(self, line):
        """Set the notebook path in the notebook, for use by other magics during execution"""

        debug_logger.info("mt_notebook_path "+line)

        self.shell.user_ns['_notebook_path'] = line.strip()


def load_ipython_extension(ipython):
    # In order to actually use these magics, you must register them with a
    # running IPython.  This code must be placed in a file that is loaded once
    # IPython is up and running:
    ip = get_ipython()
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ip.register_magics(MetatabMagic)

    #init_logging()

def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    pass
