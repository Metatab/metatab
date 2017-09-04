import unittest
from appurl import parse_app_url, match_url_classes, WebUrl, FileUrl, ZipUrl, CsvFileUrl

from metapack import MetapackDoc
from metapack.appurl import MetapackUrl, MetapackResourceUrl, MetapackDocumentUrl
from rowgenerators import get_generator
from csv import DictReader

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))

class TestUrls(unittest.TestCase):
    """Test Metapack AppUrls and Row Generators"""


    def test_metapack_urls(self):

        groups = {}

        with open(test_data('mpurls.csv')) as f:
            for l in DictReader(f):

                u = parse_app_url(l['in_url'])
                print(u)
                self.assertEqual(l['url_class'], u.__class__.__name__)
                self.assertEqual(l['url'], str(u))
                self.assertEqual(l['package_url'],str(u.package_url))

                # The second instance in each group is a resource url for the the
                # metadata url of the first instance.
                if(l['url_class']== 'MetapackDocumentUrl'):

                    self.assertNotIn(l['group'],groups)
                    self.assertEqual(str(u), str(u.metadata_url))
                else:
                    self.assertIn(l['group'], groups)
                    self.assertEqual(str(groups[l['group']]), str(u.metadata_url))

                groups[l['group']] = u

                self.assertEqual(l['metadata_url'],str(u.metadata_url))

                r = u.get_resource()

                self.assertTrue(r.inner.exists())

                t = r.get_target()
                self.assertTrue(t.inner.exists())

                # Check that the generator for the metadata gets the right number of rows
                self.assertEqual(50,len(list(u.metadata_url.generator)))

                self.assertEquals('example.com-simple_example-2017-us-1', (u.doc.find_first_value('Root.Name')))


    def test_metapack_url(self):

        # Zip

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.zip'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.zip#metadata.csv',
                         str(ud))
        self.assertIsInstance(ud, MetapackDocumentUrl)
        self.assertIsInstance(ud.inner, WebUrl)

        r = ud.get_resource()

        self.assertIsInstance(r, MetapackDocumentUrl)
        self.assertIsInstance(r.inner, ZipUrl)

        t = r.get_target()
        self.assertIsInstance(t, CsvFileUrl)

        g = get_generator(t)
        self.assertEquals(50, len(list(g)))

        self.assertEquals('example.com-simple_example-2017-us-1', (ud.doc.find_first_value('Root.Name')))

        # Excel

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.xlsx'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.xlsx#meta',
                         str(ud))
        self.assertIsInstance(ud, MetapackDocumentUrl)
        self.assertEquals('example.com-simple_example-2017-us-1', (ud.doc.find_first_value('Root.Name')))

        # Filesystem
        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv',
                         str(ud))
        self.assertIsInstance(ud, MetapackDocumentUrl)
        self.assertEquals('example.com-simple_example-2017-us-1', (ud.doc.find_first_value('Root.Name')))

        # Filesystem
        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/'
        ud = parse_app_url(us)

        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv',
                         str(ud))
        self.assertIsInstance(ud, MetapackDocumentUrl)
        self.assertEquals('example.com-simple_example-2017-us-1', (ud.doc.find_first_value('Root.Name')))

        self.assertTrue(str(ud.get_resource()).endswith(
            'library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv'))

        self.assertTrue(str(ud.get_resource().get_target()).endswith(
                       'library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv'))

        # -----
        # Resource Urls

        us = 'metapack+http://library.metatab.org.s3.amazonaws.com/example.com-simple_example-2017-us-1/metadata.csv#random_names'

        ur = parse_app_url(us)
        self.assertEqual('metapack', ur.proto)
        self.assertIsInstance(ur, MetapackResourceUrl)

        return

        r = u.get_resource()
        self.assertIsInstance(r, MetapackFileUrl)

        rs = doc.resource('random-names')

        self.assertEquals(101, len(list(rs)))

        us += "#random_names"

        u = parse_app_url(us)
        self.assertEqual('metapack', u.proto)
        self.assertIsInstance(u, MetapackWebUrl)

        print (u.get_resource())
        print(u.get_resource().get_target())

        g = get_generator(u.get_resource().get_target())

        print (len(list(rs)))

    def test_inner(self):
        u_s = 'metapack+http://public.source.civicknowledge.com.s3.amazonaws.com/example.com/geo/Parks_SD.zip#encoding=utf8'

        u = parse_app_url(u_s)

        self.assertIsInstance(u, MetapackDocumentUrl)
        self.assertIsInstance(u.inner, WebUrl)

        r = u.get_resource()
        self.assertIsInstance(r, MetapackDocumentUrl)
        self.assertIsInstance(r.inner, ZipUrl)


    def  test_fs_resource(self):

        us='metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/#random_names'

        u = parse_app_url(us)

        self.assertIsInstance(u, MetapackResourceUrl)

        self.assertEquals('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv',
                          str(u.metadata_url))

        self.assertEquals('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/',
                          str(u.package_url))

    def test_metatab_resource_zip(self):

        us='metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.zip#random-names'

        u = parse_app_url(us)

        doc = u.metadata_url.doc

        r = doc.resource(u.target_file)

        self.assertEqual(101, len(list(r)))

    def test_xlsx_parse(self):

        ru = parse_app_url('/foo/bar/bax.xlsx',
                           fragment='fragment',
                           )

        print (repr(ru))


    def test_metatab_resource_xlsx(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.xlsx#random-names'

        u = parse_app_url(us)
        self.assertIsInstance(u, MetapackResourceUrl)
        self.assertEqual('metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.xlsx#random-names', str(u))
        self.assertEqual('random-names', u.fragment)
        self.assertEqual('random-names', u.target_file)

        doc = u.doc

        r = doc.resource(u.target_file)
        ru = r.resolved_url
        print(r.value)
        print (ru)
        rur = ru.get_resource()
        print (rur)
        rurt = rur.get_target()
        print (rurt)

        self.assertEqual(101, len(list(r)))

    def test_metatab_resource_csv(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1.csv#random-names'

        u = parse_app_url(us)
        doc = u.metadata_url.doc

        r = doc.resource(u.target_segment)
        print(r.resolved_url)

        self.assertEqual(101, len(list(r)))

    def test_metatab_resource_fs(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv#random-names'

        u = parse_app_url(us)
        doc = u.metadata_url.doc

        r = u.resource
        ru = r.resolved_url

        print(ru.inner)
        print(ru.get_resource())

        return


    def test_metatab_resource_zip(self):

        us = 'metapack+http://s3.amazonaws.com/library.metatab.org/ipums.org-income_homevalue-5.zip#income_homeval'


    def test_metatab_resource_fs_pkg(self):

        us = 'metapack+http://library.metatab.org/example.com-simple_example-2017-us-1/metadata.csv'

        u = parse_app_url(us)

        print(u.package_url)

if __name__ == '__main__':
    unittest.main()
