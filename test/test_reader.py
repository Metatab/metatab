import unittest
from metatab import MetatabDoc
from metatab.doc import open_package, resolve_package_metadata_url
from rowgenerators import RowGenerator
from rowgenerators.util import reparse_url

class TestPackages(unittest.TestCase):


    def test_geo(self):

        base='/foo/bar/'
        base_exp = "file:/foo/bar/"

        for path, (package_url_exp, metadata_url_exp) in ([
            ('zip/ozone.zip',   ('zip/ozone.zip',   'zip/ozone.zip#metadata.csv')),
            ('excel/ozone.xlsx',('excel/ozone.xlsx','excel/ozone.xlsx#meta')),
            ('dir/ozone',       ('dir/ozone',       'dir/ozone/metadata.csv')),
            ('csv/ozone.csv',   ('csv', 'csv/ozone.csv')),

        ]):
            package_url, metadata_url = resolve_package_metadata_url(base+path)

            self.assertEqual(base_exp+package_url_exp, package_url )
            self.assertEqual(base_exp+metadata_url_exp, metadata_url)

            # Check that the operation is idempotent
            package_url, metadata_url = resolve_package_metadata_url(metadata_url)
            self.assertEqual(base_exp + metadata_url_exp, metadata_url)
            self.assertEqual(base_exp + package_url_exp, package_url)

            package_url, metadata_url = resolve_package_metadata_url(package_url)

            if path != 'csv/ozone.csv': # Not sure what to do about this case
                self.assertEqual(base_exp + metadata_url_exp, metadata_url)

            self.assertEqual(base_exp + package_url_exp, package_url)




        package_url_exp, metadata_url_exp = ('file:/tmp', 'file:/tmp/metadata.csv')

        package_url, metadata_url = resolve_package_metadata_url('/tmp') # '/tmp/ must be any directory that exists

        self.assertEqual(package_url_exp, package_url)
        self.assertEqual(metadata_url_exp, metadata_url)

        package_url, metadata_url = resolve_package_metadata_url('http://s3.amazonaws.com/devel.metatab.org/s3/civicknowledgecom-example-data-package')

        print(package_url, metadata_url)


    @unittest.skip('Save for later')
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
