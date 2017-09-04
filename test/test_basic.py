from __future__ import print_function

import json
import unittest
from appurl import parse_app_url
from metapack import MetapackUrl


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class MetatabTestCase(unittest.TestCase):

    def test_resolve_packages(self):


        def u(v):
            return "http://example.com/d/{}".format(v)

        def f(v):
            return "file:/d/{}".format(v)

        for us in (u('package.zip'), u('package.xlsx'), u('package.csv'), u('package/metadata.csv'),
                   f('package.zip'), f('package.xlsx'), f('package.csv'), f('package/metadata.csv'),):

            u = MetapackUrl(us)

            print(u.metadata_url)


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
        print(r.resolved_url)
        self.assertEquals('http://public.source.civicknowledge.com/example.com/sources/test_data.zip#random-names.csv',
                          str(r.resolved_url))

        for r in p.find('Root.DataFile'):

            if r.name != 'unicode-latin1':
                continue

            self.assertEquals(int(r.nrows), len(list(r)))

        self.assertEquals(['ipums', 'bordley', 'mcdonald', 'majumder'],
                          [c.name for c in p['Bibliography']])


    def test_build_package(self):

        from metapack.cli.core import make_filesystem_package, make_excel_package, \
            make_zip_package, make_csv_package, make_s3_package, PACKAGE_PREFIX, cli_init
        from metapack.util import get_cache
        from metapack import MetapackUrl
        from appurl import Downloader, get_cache
        from os import getcwd
        from os.path import dirname, join

        cli_init()

        downloader = Downloader(get_cache())

        m = MetapackUrl(test_data('packages/example.com/example-package/metadata.csv'), downloader=downloader)

        package_dir = m.join_dir(PACKAGE_PREFIX).inner

        _, fs_url, created = make_filesystem_package(m,package_dir,get_cache(), {}, False)

        print (created)

        return

        fs_url=MetapackUrl('/Volumes/Storage/proj/virt-proj/metapack/metapack/test-data/packages/example.com/'\
               'example-package/_packages/example.com-example_data_package-2017-us-1/metadata.csv',
                downloader=downloader)

        #_, url, created =  make_excel_package(fs_url,package_dir,get_cache(), {}, False)

        #_, url, created = make_zip_package(fs_url, package_dir, get_cache(), {}, False)

        #_, url, created = make_csv_package(fs_url, package_dir, get_cache(), {}, False)

        package_dir = parse_app_url('s3://test.library.civicknowledge.com/metatab', downloader=downloader)

        _, url, created = make_s3_package(fs_url, package_dir, get_cache(), {}, False)

        print(url)
        print(created)


if __name__ == '__main__':
    unittest.main()
