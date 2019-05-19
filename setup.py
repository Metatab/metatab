#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
from setuptools import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.6',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

# Setup a directory for a fake package for importing plugins

setup(
    name='metatab',
    version='0.8.0',
    description='Data format for storing structured data in spreadsheet tables',
    long_description=readme,
    packages=['metatab','metatab.templates', 'metatab.test', 'metatab.test.test-data'],

    package_data={
        '': ['*.csv','*.json','*.txt','*.ipynb',''],
    },

    install_requires=[
        'metatabdecl',
        'rowgenerators',
    ],

    # test_suite='appurl.test.test_suite',
    test_suite='nose.collector',
    tests_require=['nose', 'tabulate'],

    entry_points={
        'console_scripts': [
            'metatab=metatab.cli:metatab'
        ],

        'appurl.urls': [
            "metatab+ = metatab.appurl:MetatabUrl",
        ],

        'rowgenerators': [
            "metatab+.txt =  metatab.rowgenerators:TextRowGenerator",
            ".yaml =  metatab.rowgenerators:YamlMetatabSource"
        ]
    },

    author='Eric Busboom',
    author_email='eric@civicknowledge.com',
    url='https://github.com/Metatab/metatab-py.git',
    license='BSD',
    classifiers=classifiers,
    extras_require={
       'datapackage': ['datapackage'],
    }
)
