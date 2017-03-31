import unittest
from metatab import MetatabDoc
from metatab.doc import open_package, resolve_package_metadata_url
from rowgenerators import RowGenerator
from rowgenerators.util import reparse_url

def cache_fs():

    from fs.tempfs import TempFS

    return TempFS('rowgenerator')

class TestPackages(unittest.TestCase):

    def test_geo(self):

        url = "shape+http://s3.amazonaws.com/test.library.civicknowledge.com/census/tl_2016_us_state.geojson.zip"

        gen = RowGenerator(url=url, cache=cache_fs())

        self.assertTrue(gen.is_geo)

        self.assertEquals(-4776, int(x))


if __name__ == '__main__':
    unittest.main()
