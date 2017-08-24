from __future__ import print_function

import json
import unittest


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class MetatabTestCase(unittest.TestCase):

    def test_open_package(self):

        from metapack import open_package
        from metapack.terms import Resource

        p = open_package(test_data('packages/example.com/example-package/metadata.csv'))

        self.assertEqual(Resource, type(p.find_first('root.datafile')))

        self.assertEqual('example.com-example_data_package-2017-us-1', p.find_first('Root.Name').value)

        self.assertEqual(9, len(list(p['Resources'].find('Root.Resource'))))

        self.assertEqual(['random-names', 'renter_cost', 'simple-example-altnames', 'simple-example',
                          'unicode-latin1', 'unicode-utf8', 'renter_cost_excel07', 'renter_cost_excel97',
                          'renter_cost-2'],
                         [ r.name for r in p.find('Datafile') ])

        self.assertIsInstance (p.resource('random-names'), Resource)
        self.assertEqual('random-names', p.resource('random-names').name)

        r = p.find_first('Root.DataFile')
        self.assertEquals('http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Frandom-names.csv',
                          r.resolved_url)

        for r in p.find('Root.DataFile'):
            self.assertEquals(int(r.nrows), len(list(r)))

        self.assertEquals(['ipums', 'bordley', 'mcdonald', 'majumder'],
                          [c.name for c in p['Bibliography']])


    def test_build_package(self):

        from metapack.cli.core import make_filesystem_package, make_excel_package, \
            make_zip_package, make_csv_package, make_s3_package, PACKAGE_PREFIX
        from rowgenerators import get_cache
        from os import getcwd
        from os.path import dirname, join

        m = test_data('packages/example.com/example-package/metadata.csv')

        package_dir =join(dirname(m), PACKAGE_PREFIX)

        _, fs_url, created = make_filesystem_package(m,package_dir,get_cache(), {}, True)

        print (created)

        fs_url='/Volumes/Storage/proj/virt-proj/metapack/metapack/test-data/packages/example.com/'\
               'example-package/_packages/example.com-example_data_package-2017-us-1/metadata.csv'

        #_, url, created =  make_excel_package(fs_url,package_dir,get_cache(), {}, False)

        #_, url, created = make_zip_package(fs_url, package_dir, get_cache(), {}, False)

        #_, url, created = make_csv_package(fs_url, package_dir, get_cache(), {}, False)

        package_dir = 's3://test.library.civicknowledge.com/metatab'

        _, url, created = make_s3_package(fs_url, package_dir, get_cache(), {}, False)

        print(url)
        print(created)


if __name__ == '__main__':
    unittest.main()
