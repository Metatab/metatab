from __future__ import print_function

import json
import unittest


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class MetatabTestCase(unittest.TestCase):

    def test_open_package(self):

        from metapack import open_package

        p = open_package(test_data('packages/example.com/example-package/metadata.csv'))

        self.assertEqual('example.com-example_data_package-2017-us-1', p.find_first('Root.Name').value)

        self.assertEqual(9, len(list(p.resources())))

        self.assertEqual(['random-names', 'renter_cost', 'simple-example-altnames', 'simple-example',
                          'unicode-latin1', 'unicode-utf8', 'renter_cost_excel07', 'renter_cost_excel97',
                          'renter_cost-2'],
                         [ r.name for r in p.resources() ])

        for r in p.resources():
            self.assertEquals(int(r.nrows), len(list(r)))

        for c in p['Bibliography']:
            print(c)

    def test_build_package(self):

        from metapack.cli.core import make_filesystem_package
        from rowgenerators import get_cache

        m = test_data('packages/example.com/example-package/metadata.csv')

        _, url, created = make_filesystem_package(m, get_cache(), {}, False)


if __name__ == '__main__':
    unittest.main()
