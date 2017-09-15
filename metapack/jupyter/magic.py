# -*- coding: utf-8 -*
# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

jupyter nbextension install --py metatab.jupyter.magic

"""

from __future__ import print_function

import logging
import shlex
import sys
import docopt

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.display import  display, HTML, Latex
from collections import OrderedDict
from metapack import MetapackDoc, Downloader
from metapack.cli.core import process_schemas
from metatab.generate import TextRowGenerator
from appurl import parse_app_url
from os import makedirs, getcwd
from os.path import join, abspath, dirname, exists, normpath
from warnings import warn
from metapack.html import bibliography, data_sources

from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)

logger = logging.getLogger('user')
logger_err = logging.getLogger('cli-errors')
doc_logger = logging.getLogger('doc')
debug_logger = logging.getLogger('debug_logger')

MT_DOC_VAR = 'mt_pkg' # Namespace name for the metatab document.

@magics_class
class MetatabMagic(Magics):

    """Magics for using Metatab in Jupyter Notebooks

    """

    def _get_notebook_dir(self):
        """Return the directory the notebook is in. This is either based on the path set by
        %mt_notebook_path, or the current directory"""

        try:
            return dirname(self.shell.user_ns['_notebook_path'])
        except KeyError:
            pass

        try:
            return self.shell.user_ns['_notebook_dir']
        except KeyError:
            return getcwd()


    @property
    def mt_doc(self):
        """Return the current metatab document, which must be created with either %%metatab
        or %mt_load_package"""

        return self.shell.user_ns[MT_DOC_VAR]

    @property
    def package_dir(self):
        """Return the current metatab document, which must be created with either %%metatab
        or %mt_load_package"""

        return self.shell.user_ns['_package_dir']

    @magic_arguments()
    @argument('-s', '--show', help='After loading, display the document', action='store_true')
    @argument('-p', '--package_dir', help='Set the directory where the package will be created')
    @cell_magic
    def metatab(self, line, cell):
        """Process a cell of Metatab data, in line format. Stores document in the `mt_pkg` variable
        """

        args = parse_argstring(self.metatab, line)

        inline_doc = MetapackDoc(TextRowGenerator("Declare: metatab-latest\n" + cell))

        extant_identifier = inline_doc.get_value('Root.Identifier')

        extant_name = inline_doc.get_value('Root.Name')

        inline_doc.update_name(force=True, create_term=True)

        if not 'Resources' in inline_doc:
            inline_doc.new_section('Resources', ['Name', 'Description'])
        else:
            inline_doc['Resources'].args = \
                list(OrderedDict(
                    (c.record_term.title(), None) for t in inline_doc['Resources'].terms for c in t.children).keys())

        if not 'References' in inline_doc:
            inline_doc.new_section('References', ['Name', 'Description'])

        process_schemas(inline_doc)

        # Give all of the sections their standard args, to make the CSV versions of the doc
        # prettier

        for name, s in inline_doc.sections.items():
            try:
                s.args = inline_doc.decl_sections[name.lower()]['args']
            except KeyError:
                pass

        if args.show:
            for l in inline_doc.lines:
                print(': '.join(str(e) for e in l))

        self.shell.user_ns['_notebook_dir'] = getcwd()

        if args.package_dir:
            self.shell.user_ns['_package_dir'] = abspath(join(getcwd(), args.package_dir))
        else:
            self.shell.user_ns['_package_dir'] = join(getcwd(), inline_doc.get_value('Root.Name'))

        if extant_identifier != inline_doc.get_value('Root.Identifier'):
            print("Identifier updated. \nSet 'Identifier: {}'  in document".format(inline_doc.get_value('Root.Identifier')))

        if extant_name != inline_doc.get_value('Root.Name'):
            print("Name Changed\nSet 'Name: {}'  in document".format(inline_doc.get_value('Root.Name')))

        self.shell.user_ns[MT_DOC_VAR] = inline_doc

    @magic_arguments()
    @argument('-s', '--source', help='Force opening the source package', action='store_true')
    @line_magic
    def mt_open_package(self, line):
        """Find the metatab file for this package, open it, and load it into the namespace. """

        from metapack.jupyter.ipython import open_package, open_source_package

        args = parse_argstring(self.mt_open_package, line)
        self.shell.user_ns[MT_DOC_VAR] = open_package(self.shell.user_ns)

        self.shell.user_ns['_notebook_dir'] = getcwd()

        if self.mt_doc.package_url:
            u = parse_app_url(self.mt_doc.package_url)

    @line_magic
    def mt_import_terms(self, line):
        """Import the value of some Metatab terms into the notebook namespace """

        mt_terms = {}

        doc = self.mt_doc

        mt_terms['root.title'] = doc['Root'].find_first_value('Root.Title')
        mt_terms['root.description'] = doc['Root'].find_first_value('Root.Description')
        mt_terms['root.name'] = doc['Root'].find_first_value('Root.Name')
        mt_terms['root.identifier'] = doc['Root'].find_first_value('Root.Identifier')

        mt_terms['contacts'] = []

        for t in doc.get_section('Contacts', []):
            d = t.as_dict()
            d['type'] = t.record_term_lc
            mt_terms['contacts'].append(d)

        mt_terms['bibliography'] = []

        for t in doc.get_section('Bibliography', []):
            d = t.as_dict()
            d['type'] = t.record_term_lc
            mt_terms['bibliography'].append(d)

        mt_terms['references'] = []

        for t in doc.get_section('References', []):
            d = t.as_dict()
            d['type'] = t.record_term_lc
            mt_terms['references'].append(d)

        print('mt_terms')

        self.shell.user_ns['mt_terms'] = mt_terms

    @line_magic
    def mt_process_schemas(self, line):
        """Add Schema entries for resources to the metatab file. Does not write the doc file"""

        process_schemas(self.mt_doc)

    @magic_arguments()
    @argument('package_dir', help='Package directory')
    @argument('--feather', help='Use feather for serialization', action='store_true' )
    @line_magic
    def mt_materialize_all(self, line):
        """Materialize all of the dataframes that has been previoulsly added with mt_add_dataframe
        """

        from json import dumps

        from metapack.rowgenerator import PandasDataframeSource
        import csv

        materialized = []

        args = parse_argstring(self.mt_materialize_all, line)

        try:
            cache = self.mt_doc._cache
        except KeyError:
            cache = Downloader().cache

        for df_name, ref in self.shell.user_ns.get('_material_dataframes',{}).items():

            u = parse_app_url(args.package_dir).join(ref)

            path = u.path

            if not exists(dirname(path)):
                makedirs(dirname(path))

            df = self.shell.user_ns[df_name].fillna('')

            if args.feather:
                path = path.replace('.csv','.feather')
                df.to_feather(path)
            else:
                gen = PandasDataframeSource(u, df, cache=cache)
                with open(path, 'w') as f:
                    w = csv.writer(f)
                    w.writerows(gen)

            materialized.append({
                'df_name': df_name,
                'path': path,
                'ref':ref
            })

        # Show information about the dataframes that were materialized, so it can be harvested later
        print(dumps(materialized, indent=4))

    @magic_arguments()
    @argument('df_name', help='Dataframe name')
    @argument('dir', help='Path to output directory. Created if it does not exist')
    @argument('--feather', help='Materialize with feather', action="store_true")
    @line_magic
    def mt_materialize(self, line):
        """Materialize all of the dataframes that has been previoulsly added with mt_add_dataframe
        """

        from json import dumps
        from appurl import get_cache
        from metapack.rowgenerator import PandasDataframeSource
        import csv
        from os.path import join

        args = parse_argstring(self.mt_materialize, line)

        try:
            cache = self.mt_doc._cache
        except KeyError:
            cache = get_cache()

        if not exists(args.dir):
            makedirs(args.dir)

        if args.feather:
            path = join(args.dir, args.df_name+".feather")
            df = self.shell.user_ns[args.df_name]
            df.to_feather(path)
        else:
            path = join(args.dir, args.df_name + ".csv")
            df = self.shell.user_ns[args.df_name].fillna('')
            gen = PandasDataframeSource(parse_app_url(path), df, cache=cache)

            with open(path, 'w') as f:
                w = csv.writer(f)
                w.writerows(gen)

        print(dumps({
            'df_name': args.df_name,
            'path': path,

        }, indent=4))


    @line_magic
    def mt_show_metatab(self, line):
        """Dump the metatab file to the output, so it can be harvested after the notebook is executed"""

        try:
            for line in self.mt_doc.lines:

                if  line[1]: # Don't display "None"
                    print(': '.join(line))
        except KeyError:
            pass


    @line_magic
    def mt_add_dataframe(self, line):
        """Add a dataframe to a metatab document's data files

        Usage: mt_add_dataframe [options] <dataframe_name>

        Options:
            dataframe_name    Variable name of the dataframe
            -h, --help         Show this screen.
            -t <title>, --title <title>      Title of the dataframe
            -n <name>, --name  <name>        Metadata reference name of the dataframe
            -m , --materialize               Save the data for the dataframe


        """
        from metapack.jupyter.core import process_schema

        try:
            args = docopt.docopt(self.mt_add_dataframe.__doc__, argv=shlex.split(line))
        except docopt.DocoptExit as e:
            warn(str(e))
            return
        except SystemExit:
            return


        if not '_material_dataframes' in self.shell.user_ns:
            self.shell.user_ns['_material_dataframes'] = {}

        df = self.shell.user_ns[args['<dataframe_name>']]

        if hasattr(df, 'name'):
            # It's a Metatab dataframe, with special properties

            name = args['--name'] or df.name or args['<dataframe_name>']
            title = args['--title'] or df.title or df.desc or ''

        else:
            name = args['--name'] or args['<dataframe_name>']
            title = args['--title'] or ''

        if not name:
            warn("Failed to materialize '{}'; name must be set with .name property, or --name option".format(args['<dataframe_name>']))
            return

        try:
            doc = self.mt_doc
        except KeyError:
            doc = None

        if args['--materialize']:
            ref = 'file:data/{}.csv'.format(name)
            self.shell.user_ns['_material_dataframes'][args['<dataframe_name>']] = ref

        elif doc is not None:
            ref = 'ipynb:notebooks/{}.ipynb#{}'.format( doc.as_version(None), args['<dataframe_name>'])

        else:
            ref = None

        if doc and ref:
            if not 'Resources' in doc:
                doc.new_section('Resources')

            t = doc['Resources'].get_or_new_term("Root.Datafile", ref)

            t['name'] = name
            t['title'] = title

            process_schema(doc, doc.resource(name), df)

    @line_magic
    def mt_notebook_path(self, line):
        """Set the notebook path in the notebook, for use by other magics during execution"""

        from os import getcwd

        if not line.strip():
            # If the magic is used before any changes in directory, the notebok dir will
            # be the current directory
            self.shell.user_ns['_notebook_dir'] = getcwd()

        else:
            self.shell.user_ns['_notebook_path'] = line.strip()
            self.shell.user_ns['_notebook_dir'] = dirname(self.shell.user_ns['_notebook_path'])

    @magic_arguments()
    @argument('--format', help="Format, html or latex. Defaults to 'all' ", default='all', nargs='?', )
    @argument('converters', help="Class names for citation converters", nargs='*', )
    @line_magic
    def mt_bibliography(self, line):
        """Display, as HTML, the bibliography for the metatab document. With no argument,
         concatenate all doc, or with an arg, for only one. """

        args = parse_argstring(self.mt_bibliography, line)

        def import_converter(name):
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod

        converters = [ import_converter(e) for e in args.converters ]

        if args.format == 'html' or args.format == 'all':
            display(HTML(bibliography(self.mt_doc, converters=converters, format='html')))

        if args.format == 'latex' or args.format == 'all':
            display(Latex(bibliography(self.mt_doc, converters=converters, format='latex')))

    @magic_arguments()
    @argument('--format', help="Format, html or latex. Defaults to 'all' ", default='all', nargs='?', )
    @argument('converters', help="Class names for citation converters", nargs='*', )
    @line_magic
    def mt_data_references(self, line):
        """Display, as HTML, the bibliography for the metatab document. With no argument,
         concatenate all doc, or with an arg, for only one. """

        args = parse_argstring(self.mt_bibliography, line)

        def import_converter(name):
            components = name.split('.')
            mod = __import__(components[0])
            for comp in components[1:]:
                mod = getattr(mod, comp)
            return mod

        converters = [import_converter(e) for e in args.converters]

        if args.format == 'html' or args.format == 'all':
            display(HTML(data_sources(self.mt_doc, converters=converters, format='html')))

        if args.format == 'latex' or args.format == 'all':
            display(Latex(data_sources(self.mt_doc, converters=converters, format='latex')))

    @magic_arguments()
    @argument('lib_dir', help='Directory', nargs='?',)
    @line_magic
    def mt_lib_dir(self, line):
        """Declare a source code directory and add it to the sys path

        The argument may be a directory, a URL to a Metatab ZIP archive, or a reference to a
        Root.Reference or Root.Resource term that references a Metatab ZIP Archive

        If lib_dir is not specified, it defaults to 'lib'

        If lib_dir is a directory, the target is either at the same level as the CWD or
        one level up.

        If lib_dir is a URL, it must point to a Metatab ZIP archive that has an interal Python
        package directory. The URL may hav path elements after the ZIP archive to point
        into the ZIP archive. For instance:

            %mt_lib_dir http://s3.amazonaws.com/library.metatab.org/ipums.org-income_homevalue-5.zip

        If lib_dir is anything else, it is a reference to the name of a Root.Reference or Root.Resource term that
        references a Metatab ZIP Archive. For instance:

            %%metatab
            ...
            Section: References
            Reference: metatab+http://s3.amazonaws.com/library.metatab.org/ipums.org-income_homevalue-5.zip#income_homeval
            ...


            %mt_lib_dir incv
            from lib.incomedist import *

        """

        from os.path import splitext, basename

        args = parse_argstring(self.mt_lib_dir, line) # Its a normal string

        if not args.lib_dir:
            lib_dir = 'lib'

        else:
            lib_dir = args.lib_dir

        if not '_lib_dirs' in self.shell.user_ns:
            self.shell.user_ns['_lib_dirs'] = set()

        u = parse_app_url(lib_dir)

        # Assume files are actually directories
        # This clause will pickup both directories and reference names, but ref names should not
        # exist as directories.
        if u.proto == 'file':

            lib_dir = normpath(lib_dir).lstrip('./')

            for path in [ abspath(lib_dir), abspath(join('..',lib_dir))]:
                if exists(path) and path not in sys.path:
                    sys.path.insert(0,path)
                    self.shell.user_ns['_lib_dirs'].add(lib_dir)
                    return

        # Assume URLS are to Metapack packages on the net
        if (u.scheme == 'https' or u.scheme == 'http'):

            # The path has to be a Metatab ZIP archive, and the root directory must be the same as
            # the name of the path

            r = u.get_resource()

            pkg_name, _ = splitext(basename(r.path))

            lib_path = r.join(pkg_name).path

            if lib_path not in sys.path:
                sys.path.insert(0,lib_path)

        # Assume anything else is a Metatab Reference term name
        elif self.mt_doc.find_first('Root.Reference', name=lib_dir) or self.mt_doc.resource(lib_dir) :

            r = self.mt_doc.find_first('Root.Reference', name=lib_dir) or self.mt_doc.resource(lib_dir)

            ur = parse_app_url(r.url).inner

            return self.mt_lib_dir(str(ur))

        else:
            logger.error("Can't find library directory: '{}' ".format(lib_dir))


    @line_magic
    def mt_show_libdirs(self, line):
        """Dump the list of lib dirs as JSON"""
        import json

        if '_lib_dirs' in self.shell.user_ns:
            print(json.dumps(list(self.shell.user_ns['_lib_dirs'])))
        else:
            print(json.dumps([]))


def load_ipython_extension(ipython):
    # In order to actually use these magics, you must register them with a
    # running IPython.  This code must be placed in a file that is loaded once
    # IPython is up and running:
    ip = get_ipython()
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ip.register_magics(MetatabMagic)

    # init_logging()


def unload_ipython_extension(ipython):
    # If you want your extension to be unloadable, put that logic here.
    pass
