from __future__ import print_function

import unittest
from os.path import join, dirname

import metatab
from metatab.generate import TextRowGenerator

from metatab import MetatabDoc


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class TestUtil(unittest.TestCase):

    def test_open(self):

        doc = MetatabDoc(test_data('almost-everything.csv'))

        self.assertEquals('9FC11204-B291-4E0E-A841-5372090ADEC0', doc.find_first_value('Root.Identifier'))

        self.assertEquals('9FC11204-B291-4E0E-A841-5372090ADEC0', doc['Root'].find_first_value('Root.Identifier'))


    def test_new(self):

        import metatab.templates as tmpl

        template_path = join(dirname(tmpl.__file__), 'metatab.csv')

        doc = MetatabDoc(template_path)
        doc.cleanse()

        print(doc.as_csv().decode('utf8')[:200])

    def test_version(self):

        from textwrap import dedent


        doc = MetatabDoc(TextRowGenerator(
            dedent(
            """
            Root.Version:
            """)))

        # None because there are no Minor, Major, Patch value
        self.assertIsNone(doc.update_version())

        self.assertFalse(doc._has_semver())

        doc = MetatabDoc(TextRowGenerator(
            dedent(
                """
                Root.Version: 10
                """)))

        # None because there are no Minor, Major, Patch value
        self.assertEqual("10", doc.update_version())
        self.assertFalse(doc._has_semver())

        doc = MetatabDoc(TextRowGenerator(
            dedent(
                """
                Root.Version: 10
                Version.Patch: 5
                """)))

        # None because there are no Minor, Major, Patch value
        self.assertEqual("0.0.5", doc.update_version())
        self.assertTrue(doc._has_semver())

        doc = MetatabDoc(TextRowGenerator(
            dedent(
                """
                Root.Version: 10
                Version.Major: 2
                Version.Patch: 5
                """)))

        # None because there are no Minor, Major, Patch value
        self.assertEqual("2.0.5", doc.update_version())

        doc = MetatabDoc(TextRowGenerator(
            dedent(
                """
                Root.Name:
                Root.Origin: example.com
                Root.Dataset: foobar
                Root.Version:
                Version.Minor: 24
                Version.Major: 2
                Version.Patch: 5
                """)))

        # None because there are no Minor, Major, Patch value
        self.assertEqual("2.24.5", doc.update_version())

        doc.update_name()
        self.assertEqual('example.com-foobar-2.24', doc.get_value('Root.Name'))

if __name__ == '__main__':
    unittest.main()
