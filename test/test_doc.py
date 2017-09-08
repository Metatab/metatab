from __future__ import print_function

import unittest
from os.path import join, dirname

import metatab


from metatab import MetatabDoc

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))



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


if __name__ == '__main__':
    unittest.main()
