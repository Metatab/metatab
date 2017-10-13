# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(abspath(__file__)), 'test-data', *paths))