import unittest
from appurl import parse_app_url, match_url_classes, WebUrl, FileUrl, ZipUrl, CsvFileUrl

from metapack import MetapackDoc
from metapack.appurl import MetapackUrl, MetapackResourceUrl, MetapackDocumentUrl
from rowgenerators import get_generator
from csv import DictReader

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))

class TestIssues(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""


    def test_metapack_zip_package(self):

        us='metatab+http://s3.amazonaws.com/library.metatab.org/ipums.org-income_homevalue-5.zip#income_homeval'

        u = parse_app_url(us)

        print(u)

        doc = u.doc

        ur = doc.resource('income_homeval')

        print(doc.package_url)

        print(doc.ref)

        print(ur.resolved_url.exists())

    def test_generator_url(self):

        us = 'metapack+file:/Volumes/Storage/proj/virt-proj/metapack/metapack/test-data/packages'\
             '/example.com/simple_example-2017-us/'\
             '_packages/metadata.csv/example.com-simple_example-2017-us-1/metadata.csv#data%2Frandom-names.csv'

        u = parse_app_url(us)

        self.assertIsInstance(u, MetapackResourceUrl)


        doc = u.doc

        for r in doc.resources():
            print(r.name, r.resolved_url)
            ru = r.resolved_url
            g = ru.generator

            print(g)
            #print(len(list(r)))

    def test_fs_resource_url(self):

        us='metapack+file:/Users/eric/Library/Application Support/appurl/library.metatab.org/example.com-example_data_package-2017-us-1/metadata.csv#random-names'
        u = parse_app_url(us)

        print(u)

        t = u.get_target()
        print (t)




if __name__ == '__main__':
    unittest.main()
