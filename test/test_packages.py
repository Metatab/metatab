import unittest
from csv import DictReader
from metapack import MetapackDoc

from appurl import parse_app_url
from metapack import MetapackPackageUrl,  MetapackUrl, ResourceError, Downloader
from metapack.cli.core import (make_filesystem_package, make_s3_package, make_excel_package, make_zip_package, make_csv_package,
                                PACKAGE_PREFIX, cli_init )
from rowgenerators import get_generator, RowGeneratorError
from metatab.generate import TextRowGenerator

downloader = Downloader()



def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))



def cache_fs():

    from fs.tempfs import TempFS

    return TempFS('rowgenerator')

class TestPackages(unittest.TestCase):

    def test_geo(self):

        url = "shape+http://s3.amazonaws.com/test.library.civicknowledge.com/census/tl_2016_us_state.geojson.zip"

        gen = RowGenerator(url=url, cache=cache_fs())

        self.assertTrue(gen.is_geo)

        self.assertEquals(-4776, int(x))


    def test_resolve_resource_urls(self):
        """Test how resources are resolved in packages. The resource values must be one of:
            - A name, for excel and CSV packages
            - a path, for ZIP and filesystem packages
            - a web url, for any kind of package
        """
        with open(test_data('packages.csv')) as f:
            for i, l in enumerate(DictReader(f)):

                print(l['url'], l['target_file'])

                u = MetapackPackageUrl(l['url'], downloader=Downloader())

                if False:
                    jt = u.join_target(l['target_file'])
                    self.assertTrue(str(jt).endswith(l['joined_target']), str(jt))

                    rs = jt.get_resource()
                    self.assertTrue(str(rs).endswith(l['resource']), str(rs))

                    t = rs.get_target()
                    self.assertTrue(str(t).endswith(l['target']))

                try:
                    t = u.resolve_url(l['target_file'])
                    self.assertFalse(bool(l['resolve_error']))
                except ResourceError as e:
                    self.assertTrue(bool(l['resolve_error']))
                    continue

                self.assertEquals(str(t), l['resolved_url'])

                try:
                    g = get_generator(t.get_resource().get_target())
                    self.assertEqual(101, len(list(g)))
                    self.assertFalse(bool(l['generate_error']))
                except RowGeneratorError:
                    self.assertTrue(bool(l['generate_error']))
                    continue

    def test_package_resolve_resource_urls(self):

        m = MetapackUrl(test_data('packages/example.com/example-package/metadata.csv'), downloader=downloader)

        for r in m.doc.resources():

            #if r.name != "renter_cost_excel07":
            #    continue

            if False:
                print("=====")
                print(r.name)
                ru = r.resolved_url
                print(ru)
                rur = ru.get_resource()
                print(rur)
                t = rur.get_target()
                print(t)
                g = get_generator(r.resolved_url.get_resource().get_target())

            self.assertEqual(int(r.nrows), len(list(r)))


    def test_build_package(self):

        cli_init()

        m = MetapackUrl(test_data('packages/example.com/example-package/metadata.csv'), downloader=downloader)

        package_dir = m.package_url.join_dir(PACKAGE_PREFIX)

        cache = Downloader().cache

        _, fs_url, created = make_filesystem_package(m, package_dir, cache, {}, False)

        print(created)

        return

        fs_url = MetapackUrl('/Volumes/Storage/proj/virt-proj/metapack/metapack/test-data/packages/example.com/' \
                             'example-package/_packages/example.com-example_data_package-2017-us-1/metadata.csv',
                             downloader=downloader)

        # _, url, created =  make_excel_package(fs_url,package_dir,get_cache(), {}, False)

        # _, url, created = make_zip_package(fs_url, package_dir, get_cache(), {}, False)

        # _, url, created = make_csv_package(fs_url, package_dir, get_cache(), {}, False)

        package_dir = parse_app_url('s3://test.library.civicknowledge.com/metatab', downloader=downloader)

        _, url, created = make_s3_package(fs_url, package_dir, cache, {}, False)

        print(url)
        print(created)

    def test_build_simple_package(self):

        cli_init()

        cache = Downloader().cache

        m = MetapackUrl(test_data('packages/example.com/simple_example-2017-us/metadata.csv'), downloader=downloader)

        package_dir = m.package_url.join_dir(PACKAGE_PREFIX)
        package_dir = package_dir

        _, fs_url, created = make_filesystem_package(m, package_dir, cache, {}, True)

        fs_doc = MetapackDoc(fs_url, cache=downloader.cache)

        r = fs_doc.resource('random-names')

        # Excel

        _, url, created = make_excel_package(fs_url, package_dir, cache, {}, False)

        self.assertEquals(['random-names', 'renter_cost', 'unicode-latin1'], [r.name for r in url.doc.resources()])

        self.assertEquals( ['random-names', 'renter_cost', 'unicode-latin1'], [r.url for r in url.doc.resources()])

        # ZIP

        _, url, created = make_zip_package(fs_url, package_dir, cache, {}, False)

        self.assertEquals(['random-names', 'renter_cost', 'unicode-latin1'], [r.name for r in url.doc.resources()])

        self.assertEquals(['data/random-names.csv', 'data/renter_cost.csv', 'data/unicode-latin1.csv'],
                          [r.url for r in url.doc.resources()])

        #  CSV

        _, url, created = make_csv_package(fs_url, package_dir, cache, {}, False)

        self.assertEquals(['random-names', 'renter_cost', 'unicode-latin1'], [r.name for r in url.doc.resources()])

        self.assertEquals(
            ['com-simple_example-2017-us-2/data/random-names.csv',
             '.com-simple_example-2017-us-2/data/renter_cost.csv',
             'm-simple_example-2017-us-2/data/unicode-latin1.csv'],
            [str(r.url)[-50:] for r in url.doc.resources()])

    def test_sync_csv_package(self):

        from metapack.package import CsvPackageBuilder

        package_root = MetapackPackageUrl(
            'file:/Volumes/Storage/proj/virt-proj/metapack/metapack/test-data/packages/example.com/simple_example-2017-us/_packages',
            downloader=downloader)

        source_url = 'http://s3.amazonaws.com/library.metatab.org/example.com-simple_example-2017-us-2/metadata.csv'

        u = MetapackUrl(source_url, downloader=downloader)

        t = u.get_resource().get_target()

        p = CsvPackageBuilder(u, package_root, resource_root = u.dirname().as_type(MetapackPackageUrl))

        csv_url = p.save()

        doc = csv_url.metadata_url.doc

        for r in doc.resources():
            print(r.name, r.url)

        #with open(csv_url.path, mode='rb') as f:
        #    print (f.read())
        #    #urls.append(('csv', s3.write(f.read(), csv_url.target_file, acl)))

    def test_build_geo_package(self):

        from rowpipe.valuetype.geo import ShapeValue


        m = MetapackUrl(test_data('packages/sangis.org/sangis.org-census_regions/metadata.csv'), downloader=downloader)

        package_dir = m.package_url.join_dir(PACKAGE_PREFIX)

        _, fs_url, created = make_filesystem_package(m, package_dir, downloader.cache, {}, True)

        print(fs_url)

        doc = MetapackDoc(fs_url)

        r = doc.resource('sra')

        rows =  list(r.iterdict)

        self.assertEqual(41,len(rows))

        self.assertIsInstance(rows[1]['geometry'], ShapeValue)

    def test_build_transform_package(self):

        from rowpipe.valuetype.geo import ShapeValue

        m = MetapackUrl(test_data('packages/example.com/example.com-transforms/metadata.csv'), downloader=downloader)

        package_dir = m.package_url.join_dir(PACKAGE_PREFIX)

        _, fs_url, created = make_filesystem_package(m, package_dir, downloader.cache, {}, False)

        print(fs_url)



    def test_read_geo_packages(self):
        from pandasreporter.dataframe import CensusDataFrame
        from metapack.jupyter.pandas import MetatabDataFrame
        from metapack.jupyter.pandas import MetatabSeries
        from geopandas.geoseries import GeoSeries
        from rowpipe.valuetype.geo import ShapeValue

        with open(test_data('line-oriented-doc.txt')) as f:
            text = f.read()

        doc = MetapackDoc(TextRowGenerator("Declare: metatab-latest\n" + text))

        r = doc.reference('B09020')
        df = r.dataframe()

        self.assertIsInstance(df, CensusDataFrame)

        r = doc.reference('sra_geo')
        df = r.dataframe()

        self.assertIsInstance(df, MetatabDataFrame)

        self.assertIsInstance(df.geometry, MetatabSeries)

        self.assertIsInstance(df.geo.geometry, GeoSeries)

        row = next(r.iterdict)

        self.assertIsInstance(row['geometry'], ShapeValue)

    def test_program_resource(self):


        m = MetapackUrl(test_data('packages/example.com/example-package/metadata.csv'), downloader=downloader)

        doc = MetapackDoc(m)

        r = doc.resource('rowgen')

        self.assertEqual('program+file:scripts/rowgen.py', str(r.url))

        print(r.resolved_url)

        g = r.row_generator

        print(type(g))

        for row in r:
            print(row)

    def test_fixed_resource(self):
        from itertools import islice
        from rowgenerators.generator.fixed import FixedSource

        m = MetapackUrl(test_data('packages/example.com/example-package/metadata.csv'), downloader=downloader)

        doc = MetapackDoc(m)

        r = doc.resource('simple-fixed')

        self.assertEqual('fixed+http://public.source.civicknowledge.com/example.com/sources/simple-example.txt', str(r.url))
        self.assertEqual('fixed+http://public.source.civicknowledge.com/example.com/sources/simple-example.txt',
                         str(r.resolved_url))

        g = r.row_generator

        print(r.row_processor_table())

        self.assertIsInstance(g, FixedSource)

        rows = list(islice(r, 10))

        print('----')
        for row in rows:
            print (row)

        self.assertEqual('f02d53a3-6bbc-4095-a889-c4dde0ccf5',rows[5][1])

if __name__ == '__main__':
    unittest.main()
