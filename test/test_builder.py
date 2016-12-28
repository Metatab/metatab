import unittest

import collections
import json
from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator, MetatabDoc

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))



class TestBuilder(unittest.TestCase):

    import json

    def test_basic(self):
        fn = test_data('example1.csv')

        doc = MetatabDoc().load_csv(fn)

        doc.write_csv('/tmp/metatab.csv')

if __name__ == '__main__':
    unittest.main()
