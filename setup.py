#!/usr/bin/env python
# -*- coding: utf-8 -*-

import imp
import os
import sys
import shutil
import glob
from distutils.command import sdist as sdist_module
from os.path import dirname, abspath, join, isdir

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

ps_meta = imp.load_source('_meta', 'metatab/_meta.py')

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

class sdist(sdist_module.sdist):
    def run(self):
        dcl = imp.load_source('dcl', 'metatab/declarations/__init__.py')
        dest_dir = abspath(dirname(dcl.__file__))

        src_dir = join(dirname(dirname(abspath(__file__))),'metatab','declarations')

        if not isdir(src_dir):
            raise IOError("Can't build without metatab package at same level as this module\n "
                          "https://github.com/CivicKnowledge/metatab.git")

        for fn in glob.glob(join(src_dir,'*.csv')):
            print("Copying {} to {}".format(fn, dest_dir))
            shutil.copy(fn, dest_dir)

        return sdist_module.sdist.run(self)

setup(
    name='metatab',
    version=ps_meta.__version__,
    description='Data format for storing structured data in spreadsheet tables',
    long_description=readme,
    packages=['metatab', 'test', 'metatab.declarations', 'metatab.templates'],
    package_data={'metatab.declarations': ['*.csv'],
                  'metatab.templates': ['*.csv']},

    zip_safe=False,
    install_requires=[
        'six',
        'unicodecsv',
        'pyyaml',
        'datapackage',
        'rowgenerators',
        'rowpipe',
        'boto3'
    ],

    
    entry_points={
        'console_scripts': [
            'metatab=metatab.cli:metatab',
            'metapack=metatab.cli:metapack',
        ],
    },

    author=ps_meta.__author__,
    author_email=ps_meta.__author__,
    url='https://github.com/CivicKnowledge/metatab-py.git',
    license='BSD',
    classifiers=classifiers,
    extras_require={
        'test': ['datapackage'],

    },

    cmdclass={
        'sdist': sdist,
    },

)
