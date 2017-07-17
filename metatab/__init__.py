# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE
"""
Record objects for the Simple Data Package format.
"""

from .parser import *
from .serialize import *
from .exc import *
from .generate import *
from .doc import *
from .package import *
from .s3 import set_s3_profile
import metatab.ipython


from metatab.jupyter.magic import load_ipython_extension, unload_ipython_extension
