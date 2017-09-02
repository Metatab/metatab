# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE
"""
Record objects for the Simple Data Package format.
"""

from .serialize import *
from .exc import *
from .doc import MetapackDoc
from .package import open_package


from metapack.jupyter.magic import load_ipython_extension, unload_ipython_extension
