import os
from metatab.server import app
import unittest
import tempfile

class BasicTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_parse(self):
        import json
        from os.path import join, dirname
        import csv

        fn = join(dirname(__file__), '../test-data', 'example1-web.csv')

        with open(fn) as f:
            str_data = f.read();

        with open(fn) as f:
            row_data = [row for row in csv.reader(f)]

        response = self.app.post('/v1/parse',
                                 data=json.dumps(row_data),
                                 content_type='application/json')

        self.assertListEqual([u'datafile', u'description', u'format', u'title', u'documentation', u'spatialgrain',
                              u'wrangler', u'note', u'creator', u'version', u'obsoletes', u'spatial', u'table',
                              u'identifier', u'homepage', u'time'],
                             json.loads(response.data)['result'].keys())

        self.assertListEqual([], json.loads(response.data)['errors'])

        with open(fn) as f:
            response = self.app.post('/v1/parse',data=f.read(),content_type='text/csv')

            self.assertListEqual([u'datafile', u'description', u'format', u'title', u'documentation', u'spatialgrain',
                                  u'wrangler', u'note', u'creator', u'version', u'obsoletes', u'spatial', u'table',
                                  u'identifier', u'homepage', u'time'],
                                 json.loads(response.data)['result'].keys())

            self.assertListEqual([], json.loads(response.data)['errors'])

        fn = join(dirname(__file__), 'data', 'example1-web.csv')
        with open(fn) as f:
            response = self.app.post('/v1/parse', data=f.read(), content_type='text/csv')

            self.assertListEqual([u'datafile', u'description', u'format', u'title', u'documentation', u'spatialgrain',
                                  u'wrangler', u'note', u'creator', u'version', u'obsoletes', u'spatial', u'table',
                                  u'identifier', u'homepage', u'time'],
                                 json.loads(response.data)['result'].keys())

            self.assertListEqual([], json.loads(response.data)['errors'])


if __name__ == '__main__':
    unittest.main()