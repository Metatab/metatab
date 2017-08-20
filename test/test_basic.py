from __future__ import print_function

import json
import unittest


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class MetatabTestCase(unittest.TestCase):

    def test_open_package(self):

        from metapack import open_package

        p = open_package(test_data('packages/example.com/example.com-test_package/metadata.csv'))

        self.assertEqual('example.com-test_package-1', p.find_first('Root.Name').value)


    def test_build_package(self):



        _, url, created = make_filesystem_package(m.mt_file, m.cache, env, skip_if_exists)



if __name__ == '__main__':
    unittest.main()
