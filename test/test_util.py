from __future__ import print_function

import json
import unittest

from metatab import IncludeError
from metatab import MetatabRowGenerator

from metatab.util import flatten, declaration_path
from metatab import TermParser, CsvPathRowGenerator
from metatab.terms import Term
from collections import defaultdict

import json
from os.path import exists
from metatab import MetatabDoc

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class TestUtil(unittest.TestCase):

    def test_import(self):
        from metatab.util import import_name_or_class
        from metatab.terms import Resource

        for e in ("metatab.terms.Resource", Resource):
            self.assertEqual(import_name_or_class(e), Resource)


if __name__ == '__main__':
    unittest.main()
