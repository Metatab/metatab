# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Functions for executing Jupyter notebooks
"""


def execute(nb_path, env):
    """Convert the notebook to a python script and execute it, returning the local context
    as a dict"""

    from nbconvert.exporters import get_exporter

    preprocessors = ['metatab.jupyter.preprocessors.RemoveMagics']

    exporter = get_exporter('python')(preprocessors=preprocessors)

    (script, notebook) = exporter.from_filename(filename=nb_path)

    exec(compile(script.replace('# coding: utf-8', ''), 'script', 'exec'), env)

    return env