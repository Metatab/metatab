import logging
import sys
from itertools import islice
from textwrap import dedent

import metatab.jupyter
import nbformat
from metatab import MetatabDoc
from metatab.jupyter.core import get_package_dir, logger, debug_logger
from metatab.jupyter.markdown import MarkdownExporter
from nbconvert.exporters.html import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError
from nbconvert.writers.files import FilesWriter
from nbformat.notebooknode import from_dict
from os.path import dirname, abspath
from os.path import join

from traitlets.config import Config
from .preprocessors import RemoveMetatab


def write_documentation(nb_path):

    with open(nb_path) as f:
        nb = nbformat.reads(f.read(), as_version=4)

    c = Config()

    c.MarkdownExporter.preprocessors = ['metatab.jupyter.preprocessors.RemoveMagics']

    c.HTMLExporter.preprocessors = ['nbconvert.preprocessors.ExtractOutputPreprocessor',
                                    'metatab.jupyter.preprocessors.NoShowInput',
                                    'metatab.jupyter.preprocessors.RemoveMetatab'
                                    ]

    c.HTMLExporter.exclude_input_prompt = True
    c.HTMLExporter.exclude_output_prompt = True

    c.HTMLExporter.template_path = ['.', dirname(metatab.jupyter.__file__)]

    pkg_dir, pkg_name = get_package_dir(nb_path)
    fw = FilesWriter(build_directory=join(pkg_dir, 'documentation'))

    exp = MarkdownExporter(config=c)
    (md_body, _) = exp.from_notebook_node(nb)
    fw.write(md_body, {'output_extension': '.md'}, 'documentation')

    html_exp = HTMLExporter(config=c, template_file='hide_input_html_basic.tpl')
    (html_basic_body, resources) = html_exp.from_notebook_node(nb)
    fw.write(html_basic_body, resources, 'html_body')

    html_exp = HTMLExporter(config=c, template_file='hide_input_html.tpl')
    (html_full_body, _) = html_exp.from_notebook_node(nb)
    fw.write(html_full_body, {'output_extension': '.html'}, 'documentation')


def write_notebook(nb_path):
    """Executes the notebook, exports the Metatab data in it, and writes the notebook into the package"""


    nb_path = abspath(nb_path)
    nb_dir = dirname(nb_path)+'/'

    pkg_dir, pkg_name = get_package_dir(nb_path)

    with open(nb_path) as f:
        nb = nbformat.reads(f.read(), as_version=4)

    nb.cells.append(from_dict({
        'cell_type': 'code',
        'metadata': {},
        'source': dedent("""
        %mt_notebook_path {nb_path}
        %mt_write_metatab {pkg_dir}
        %mt_process_schemas
        """.format(nb_path=nb_path, pkg_dir=pkg_dir+'/'))
    }))

    debug_logger.info('Executing')

    ep = ExecutePreprocessor(timeout=600)

    out_path = join(pkg_dir, 'notebooks', pkg_name + '.ipynb')

    try:
        r = ep.preprocess(nb, {'metadata': {'path': nb_dir}})
        RemoveMetatab().preprocess(nb, {})
    except CellExecutionError as e:

        raise CellExecutionError("Errors executing noteboook. See output at {} for details.\n{}"
                                 .format(out_path, ''))
    finally:
        with open(out_path, mode='wt') as f:
            nbformat.write(nb, f)


def process_schema(doc, resource, df):
    from rowgenerators import SourceError
    from requests.exceptions import ConnectionError

    from metatab.cli.core import extract_path_name, alt_col_name, type_map
    from tableintuit import TypeIntuiter
    from rowgenerators import PandasDataframeSource, SourceSpec

    try:
        doc['Schema']
    except KeyError:
        doc.new_section('Schema', ['DataType', 'Altname', 'Description'])


    schema_name = resource.get_value('schema', resource.get_value('name'))

    schema_term = doc.find_first(term='Table', value=schema_name, section='Schema')

    if schema_term:
        logger.info("Found table for '{}'; skipping".format(schema_name))
        return


    path, name = extract_path_name(resource.url)

    logger.info("Processing {}".format(resource.url))

    si = PandasDataframeSource(SourceSpec(resource.url), df, cache=doc._cache,)

    try:
        ti = TypeIntuiter().run(si)
    except SourceError as e:
        logger.warn("Failed to process '{}'; {}".format(path, e))
        return
    except ConnectionError as e:
        logger.warn("Failed to download '{}'; {}".format(path, e))
        return

    table = doc['Schema'].new_term('Table', schema_name)

    logger.info("Adding table '{}' to metatab schema".format(schema_name))

    for i, c in enumerate(ti.to_rows()):

        raw_alt_name = alt_col_name(c['header'], i)
        alt_name = raw_alt_name if raw_alt_name != c['header'] else ''

        t = table.new_child('Column', c['header'],
                        datatype=type_map.get(c['resolved_type'], c['resolved_type']),
                        altname=alt_name,
                        description=df[c['header']].description if  df[c['header']].description else ''
                        )