# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Functions for converting Jupyter notebooks
"""
from os import getcwd
from os.path import abspath
from os.path import normpath, exists

import nbformat
from nbconvert.writers import FilesWriter
from traitlets.config import Config

from appurl import parse_app_url
from metatab import DEFAULT_METATAB_FILE
from metapack import MetapackDoc
from metapack.cli.core import prt, err
from metapack.util import ensure_dir, copytree
from metapack.jupyter.core import logger
from metapack.jupyter.exporters import NotebookExecutor, DocumentationExporter
from metapack.jupyter.preprocessors import ExtractInlineMetatabDoc
from rowgenerators.util import fs_join as join



def convert_documentation(m):
    """Run only the document conversion portion of the notebook conversion

      The final document will not be completel
    """


    nb_path = parse_app_url(m.mt_file).path

    with open(nb_path) as f:
        nb = nbformat.reads(f.read(), as_version=4)

    doc = ExtractInlineMetatabDoc().run(nb)

    package_name = doc.as_version(None)

    output_dir = join(getcwd(), package_name)

    de = DocumentationExporter(config=Config(), log=logger, metadata=doc_metadata(doc))
    prt('Converting documentation')
    output, resources = de.from_filename(nb_path)

    fw = FilesWriter()

    fw.build_directory = join(output_dir,'docs')
    fw.write(output, resources, notebook_name='notebook')
    prt("Wrote documentation to {}".format(fw.build_directory))



def convert_notebook(m):


    prt('Convert notebook to Metatab source package')

    u = parse_app_url(m.mtfile_arg)

    nb_path = u.path

    if not exists(nb_path):
        err("Notebook path does not exist: '{}' ".format(nb_path))

    c = Config()

    pe = NotebookExecutor(config=c, log=logger)

    prt('Running the notebook')
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

    doc = MetapackDoc(new_mt_file)

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