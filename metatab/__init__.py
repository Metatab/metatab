# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE
"""
Record objects for the Simple Data Package format.
"""

# default metadata file
DEFAULT_METATAB_FILE = 'metadata.csv'
LINES_METATAB_FILE = 'metadata.txt'
IPYNB_METATAB_FILE = 'metadata.ipynb'

from .parser import *
from .exc import *
from .doc import MetatabDoc
from .resolver import WebResolver

from pkg_resources import get_distribution, DistributionNotFound
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

