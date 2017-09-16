#!/usr/bin/env python
# -*- coding: utf-8 -*-

import imp
import os
import sys
import shutil
import glob
from distutils.command import sdist as sdist_module
from os.path import dirname, abspath, join, isdir

try:
    from site import getsitepackages
    plugin_base_dir = [e for e in getsitepackages() if e.startswith(sys.prefix)][0]
except ImportError:
    # Virtualenvs have their own copy of site.py, which is empty/
    plugin_base_dir = os.path.join(sys.prefix, "lib","python%d.%d" % sys.version_info[:2],
                 "site-packages")

from setuptools import find_packages

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

ps_meta = imp.load_source('_meta', 'metapack/_meta.py')

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.4',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    name='metapack',
    version=ps_meta.__version__,
    description='Data packaging system using Metatab',
    long_description=readme,
    packages=['metapack', 'test', 'metapack.jupyter', 'metapack.cli'],
    package_data={'metatab.jupyter': ['*.csv']},
    zip_safe=False,
    install_requires=[
        'six',
        'unicodecsv',
        'pyyaml',
        'datapackage',
        'bs4',
        'markdown',
        'ckanapi',
        'boto3',
        'rowgenerators>=0.3.2',
        'rowpipe>=0.1.2',
        'tableintuit>=0.0.6',
        'geoid>=1.0.4',
        'metapack',
        'nbconvert',
        'IPython',
        'nameparser',
        'pybtex'

    ],

    entry_points={
        'console_scripts': [
            #'metapack=metapack.cli.metapack:metapack',
            'mt=metapack.cli.mt:mt',
            'metakan=metapack.cli.metakan:metakan',
            'metasync=metapack.cli.metasync:metasync',
            'metaworld=metapack.cli.metaworld:metaworld',
            'metaaws=metapack.cli.metaaws:metaaws',
            'metasql=metapack.cli.metasql:metasql'

        ],
        'nbconvert.exporters': [
            'metapack = metapack.jupyter:MetapackExporter',
        ],
        'appurl.urls' : [
            "metapack+ = metapack.appurl:MetapackUrl",
            "metatab+ = metapack.appurl:MetapackUrl",
            ".ipynb = metapack.appurl:JupyterNotebookUrl"

        ],
        'rowgenerators': [

            "<MetapackUrl> = metapack.rowgenerator:MetapackGenerator",
            "<JupyterNotebookUrl> = metapack.rowgenerator:JupyterNotebookSource",

        ],
        'mt.subcommands': [
            'pack=metapack.cli.metapack:metapack',
            's3=metapack.cli.metas3:metas3',
            'ckan=metapack.cli.metakan:metakan'
        ]


    },

    include_package_data=True,
    author=ps_meta.__author__,
    author_email=ps_meta.__author__,
    url='https://github.com/CivicKnowledge/metapack.git',
    license='BSD',
    classifiers=classifiers,
    extras_require={
        'test': ['datapackage'],
        'geo': ['fiona','shapely','pyproj'],

    },

)
