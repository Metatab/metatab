import unittest

from metatab.generate import *

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))

def test_url(*paths):
    from os.path import dirname, join, abspath

    t = "https://raw.githubusercontent.com/CivicKnowledge/metatab-py/master/test-data/{}"

    return t.format(join(*paths))

def data_string(*paths):

    with open(test_data(*paths)) as f:
        return f.read()

def data_rows(*paths):
    import csv
    with open(test_data(*paths)) as f:
        return list(csv.reader(f))

class GenerationTestCases(unittest.TestCase):

    def test_basic(self):

        files = [
            ('example1.csv', 56),
            ('example2.csv', 10)
        ]

        for f, size in files:
            for clz, sourcef in ( (CsvPathRowGenerator, test_data),
                             (CsvUrlRowGenerator, test_url),
                             (MetatabRowGenerator,data_rows) ):

                rows = tuple(clz(sourcef(f)))
                self.assertEqual(size, len(rows))

                rows = tuple(generateRows(sourcef(f)))
                self.assertEqual(size, len(rows))



if __name__ == '__main__':
    unittest.main()
