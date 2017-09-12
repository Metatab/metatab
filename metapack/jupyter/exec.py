# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Functions for executing Jupyter notebooks
"""


def x_execute(nb_path, env):
    """Convert the notebook to a python script and execute it, returning the local context
    as a dict"""

    from nbconvert.exporters import get_exporter

    preprocessors = ['metatab.jupyter.preprocessors.RemoveMagics']

    exporter = get_exporter('python')(preprocessors=preprocessors)

    (script, notebook) = exporter.from_filename(filename=nb_path)

    exec(compile(script.replace('# coding: utf-8', ''), 'script', 'exec'), env)

    return env


def execute_notebook(nb_path, pkg_dir, dataframes, write_notebook=False):
    """
    Execute a notebook after adding the prolog and epilog. Can also add %mt_materialize magics to
    write dataframes to files

    :param nb_path: path to a notebook.
    :param pkg_dir: Directory to which dataframes are materialized
    :param dataframes: List of names of dataframes to materialize
    :return: a Notebook object
    """

    import nbformat
    from metapack.jupyter.preprocessors import AddEpilog
    from metapack.jupyter.exporters import ExecutePreprocessor, Config
    from os.path import dirname, join, splitext, basename
    from nbconvert.preprocessors.execute import CellExecutionError

    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=4)

    root, ext = splitext(basename(nb_path))

    c = Config()

    nb, resources = AddEpilog(config=c, pkg_dir=pkg_dir,
                              dataframes=dataframes
                              ).preprocess(nb, {})

    try:
        ep = ExecutePreprocessor(config=c)

        nb, _ = ep.preprocess(nb, {'metadata': {'path': dirname(nb_path)}})
    except CellExecutionError as e:
        err_nb_path = join(dirname(nb_path), root + '-errors' + ext)
        with open(err_nb_path, 'wt') as f:
            nbformat.write(nb, f)

        raise CellExecutionError("Errors executing noteboook. See notebook at {} for details.\n{}"
                                 .format(err_nb_path, ''))

    if write_notebook:
        if write_notebook is True:
            exec_nb_path = join(dirname(nb_path), root + '-executed' + ext)
        else:
            exec_nb_path = write_notebook

        with open(exec_nb_path, 'wt') as f:
            nbformat.write(nb, f)

    return nb