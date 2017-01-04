import unittest

import collections
import json
from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator, MetatabDoc
from metatab.util import flatten

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class TestBuilder(unittest.TestCase):

    def compare_dict(self, a, b):
        fa = set('{}={}'.format(k, v) for k, v in flatten(a));
        fb = set('{}={}'.format(k, v) for k, v in flatten(b));

        errors = len(fa - fb) + len(fb - fa)

        if errors:
            print("=== ERRORS ===")

        if len(fa - fb):
            print("In b but not a")
            for e in sorted(fa - fb):
                print('    ', e)

        if len(fb - fa):
            print("In a but not b")
            for e in sorted(fb - fa):
                print('    ', e)

        self.assertEqual(0, errors)

    def test_basic(self):

        fn = test_data('example1.csv')

        doc = MetatabDoc().load_csv(fn)

        doc.write_csv('/tmp/metatab.csv')

        ti1 = TermInterpreter(TermGenerator(CsvPathRowGenerator(test_data('example1.csv'))))
        ti2 = TermInterpreter(TermGenerator(CsvPathRowGenerator(test_data('/tmp/metatab.csv'))))
        ti3 = doc.term_interpreter

        self.compare_dict(ti1.as_dict(), ti2.as_dict())
        self.compare_dict(ti1.as_dict(), ti3.as_dict())
        self.compare_dict(ti2.as_dict(), ti3.as_dict())

        self.assertNotEquals('Foobar', doc['Root']['Identifier'].value)

        doc['Root']['Identifier'] = 'Foobar'

        self.assertEquals('Foobar', doc['Root']['Identifier'].value)

    def test_sections(self):

        doc = MetatabDoc()

        s = doc.new_section("SectionOne","A B C".split())

        print doc.sections

        print doc.as_dict()

if __name__ == '__main__':
    unittest.main()
