#!/usr/bin/env python
# -*- coding: utf-8 -*-

import imp
import os
import sys

from os.path import  join


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

ps_meta = imp.load_source('_meta', 'metatab/_meta.py')

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.4',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

# Setup a directory for a fake package for importing plugins

setup(
    name='metatab',
    version=ps_meta.__version__,
    description='Data format for storing structured data in spreadsheet tables',
    long_description=readme,
    packages=['metatab'],

    install_requires=[
        'six',
        'unicodecsv',
        #'pyyaml',
        #'datapackage',
        #'bs4',
        #'markdown',
        #'ckanapi',
        #'boto3',
        'rowgenerators>=0.3.2',
        #'rowpipe>=0.1.2',
        #'tableintuit>=0.0.6',
        #'geoid>=1.0.4'
        'metatabdecl',
        'deprecation'

    ],

    entry_points={
        'console_scripts': [
            'metatab=metatab.cli:metatab'

        ]
    },

    include_package_data=True,

    author=ps_meta.__author__,
    author_email=ps_meta.__author__,
    url='https://github.com/CivicKnowledge/metatab-py.git',
    license='BSD',
    classifiers=classifiers,
    extras_require={
       'datapackage': ['datapackage'],
       # 'geo': ['fiona','shapely','pyproj'],

    }
)
