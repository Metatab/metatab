import unittest
from metatab import MetatabDoc
from metatab.doc import open_package
from rowgenerators import RowGenerator

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)

    def test_zip_package_reader(self):

        base = '/Volumes/Storage/proj/virt/metatab3/metatab-packages/cdph.ca.gov-hci/packages/'

        for bf in ([
                base + 'zip/ozone.zip',
                base + 'excel/ozone.xlsx',
                base + 'csv/ozone.csv',
                base + 'dir/ozone'

        ]):

            doc = open_package(bf)

            print ("---")
            print(bf, len(list(doc.terms)))

            for r in doc.resources(term='Root.Datafile'):
                print(r.resolved_url, len(list(r.generator)))


if __name__ == '__main__':
    unittest.main()
