# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Common support for jupyter notebooks.
"""
import nbformat
from os.path import join, dirname
from os import makedirs
import logging

logger = logging.getLogger('user')
err_logger = logging.getLogger('cli-errors')
debug_logger = logging.getLogger('debug')
doc_logger = logging.getLogger('doc')

log_init = False

def init_logging(log_level=logging.INFO):

    global log_init

    if log_init:
        return

    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter('%(message)s'))
    out_hdlr.setLevel(log_level)
    logger.addHandler(out_hdlr)
    logger.setLevel(log_level)

    out_hdlr = logging.StreamHandler(sys.stderr)
    out_hdlr.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    out_hdlr.setLevel(logging.WARN)
    err_logger.addHandler(out_hdlr)
    err_logger.setLevel(logging.WARN)

    out_hdlr = logging.StreamHandler(sys.stderr)
    out_hdlr.setFormatter(logging.Formatter('DBG %(levelname)s: %(message)s'))
    out_hdlr.setLevel(logging.INFO)
    debug_logger.addHandler(out_hdlr)
    debug_logger.setLevel(logging.CRITICAL)

    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter('%(message)s'))
    out_hdlr.setLevel(log_level)
    doc_logger.addHandler(out_hdlr)
    doc_logger.setLevel(log_level)

    log_init = True



def ensure_source_package_dir(nb_path, pkg_name):
    """Ensure all of the important directories in a source package exist"""

    pkg_path = join(dirname(nb_path), pkg_name)

    makedirs(join(pkg_path,'notebooks'),exist_ok=True)
    makedirs(join(pkg_path, 'documentation'), exist_ok=True)

    return pkg_path


def get_metatab_doc(nb_path):
    """Read a notebook and extract the metatab document. Only returns the first document"""

    from metatab.generate import TextRowGenerator, CsvDataRowGenerator
    from metatab import MetatabDoc

    with open(nb_path) as f:
        nb = nbformat.reads(f.read(), as_version=4)

    for cell in nb.cells:
        source = ''.join(cell['source']).strip()
        if source.startswith('%%metatab'):
            return MetatabDoc(TextRowGenerator(source))


def get_package_dir(nb_path):

    doc = get_metatab_doc(nb_path)
    doc.update_name(force=True, create_term=True)
    pkg_name = doc['Root'].get_value('Root.Name')
    assert pkg_name

    return ensure_source_package_dir(nb_path, pkg_name), pkg_name