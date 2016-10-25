#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools.command.test import test as TestCommand
from setuptools import find_packages
import uuid
import imp

from pip.req import parse_requirements

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

ps_meta = imp.load_source('_meta', 'metatab/__meta__.py')

packages = find_packages()

tests_require = install_requires = parse_requirements('requirements.txt', session=uuid.uuid1())

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Topic :: Software Development :: Libraries :: Python Modules',
]


setup(
    name='metatab',
    version=ps_meta.__version__,
    description='Data format for storing structured data in spreadsheet tables',
    long_description=readme,
    packages=packages,
    include_package_data=True,
    zip_safe=False,
    install_requires=[x for x in reversed([str(x.req) for x in install_requires])],
    tests_require=[x for x in reversed([str(x.req) for x in tests_require])],
    entry_points={
        'console_scripts': [
            'metatab=metatab.cli.main:main',
        ],
    },

    author=ps_meta.__author__,
    author_email=ps_meta.__author__,
    url='https://github.com/CivicKnowledge/metatab.git',
    license='MIT',
    classifiers=classifiers
)
