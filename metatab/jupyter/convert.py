# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Functions for converting Jupyter notebooks
"""
from metatab import DEFAULT_METATAB_FILE, MetatabDoc
from metatab.cli.core import prt
from metatab.util import ensure_dir, copytree
from os.path import abspath
from os import getcwd
from rowgenerators import Url
from rowgenerators.util import fs_join as join


def convert_documentation(m):
    """Run only the document conversion portion of the notebook conversion

      The final document will not be completel
    """
    from .exporters import PackageExporter, DocumentationExporter
    from .preprocessors import ExtractInlineMetatabDoc
    from traitlets.config import Config
    from .core import logger
    from nbconvert.writers import FilesWriter
    import nbformat

    nb_path = Url(m.mt_file).parts.path

    with open(nb_path) as f:
        nb = nbformat.reads(f.read(), as_version=4)

    doc = ExtractInlineMetatabDoc().run(nb)

    package_name = doc.as_version(None).find_first_value('Root.Name')

    output_dir = join(getcwd(), package_name)

    de = DocumentationExporter(config=Config(), log=logger, metadata=doc_metadata(doc))
    prt('Converting documentation')
    output, resources = de.from_filename(nb_path)

    fw = FilesWriter()

    fw.build_directory = join(output_dir,'docs')
    fw.write(output, resources, notebook_name='notebook')
    prt("Wrote documentation to {}".format(fw.build_directory))


def convert_notebook(m):

    from .core import logger
    from traitlets.config import Config
    from metatab.jupyter.exporters import PackageExporter, DocumentationExporter
    from nbconvert.writers import FilesWriter
    from os.path import normpath

    prt('Convert notebook to Metatab source package')
    nb_path = Url(m.mt_file).parts.path

    c = Config()

    pe = PackageExporter(config=c, log=logger)

    prt('Runing the notebook')
    output, resources = pe.from_filename(nb_path)

    fw = FilesWriter()
    fw.build_directory = pe.output_dir

    fw.write(output, resources, notebook_name=DEFAULT_METATAB_FILE)

    de = DocumentationExporter(config=c, log=logger, metadata=doc_metadata(pe.doc))

    prt('Exporting documentation')
    output, resources = de.from_filename(nb_path)

    fw.build_directory = join(pe.output_dir,'docs')
    fw.write(output, resources, notebook_name='notebook')

    new_mt_file = join(pe.output_dir, DEFAULT_METATAB_FILE)

    doc = MetatabDoc(new_mt_file)

    de.update_metatab(doc, resources)


    for lib_dir in pe.lib_dirs:

        lib_dir = normpath(lib_dir).lstrip('./')

        doc['Resources'].new_term("Root.PythonLib", lib_dir)

        path = abspath(lib_dir)
        dest = join(pe.output_dir, lib_dir)

        ensure_dir(dest)
        copytree(path, join(pe.output_dir, lib_dir))


    doc.write_csv()

    # Reset the input to use the new data

    prt('Running with new package file: {}'.format(new_mt_file))
    m.init_stage2(new_mt_file, '')


def doc_metadata(doc):
    """Create a metadata dict from a MetatabDoc, for Document conversion"""

    r = doc['Root'].as_dict()
    r.update(doc['Contacts'].as_dict())
    r['author'] = r.get('author', r.get('creator', r.get('wrangler')))

    return r