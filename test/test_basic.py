from __future__ import print_function

import json
import unittest

from metatab import IncludeError
from metatab import RowGenerator, TermParser, CsvPathRowGenerator, parse_file
from metatab import MetatabDoc
from metatab.util import flatten
from metatab import TermParser, CsvPathRowGenerator, Serializer, Term
from collections import defaultdict


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class MyTestCase(unittest.TestCase):
    def compare_dict(self, a, b):
        fa = set('{}={}'.format(k, v) for k, v in flatten(a));
        fb = set('{}={}'.format(k, v) for k, v in flatten(b));

        # The declare lines move around a lot, and rarely indicate an error
        fa = { e for e in fa if not e.startswith('declare=')}
        fb = {e for e in fa if not e.startswith('declare=')}

        errors = len(fa - fb) + len(fb - fa)

        if errors:
            print("=== ERRORS ===")

        if len(fa - fb):
            print("In b but not a")
            for e in sorted(fa - fb):
                print('    ', e)

        if len(fb - fa):
            print("In a but not b")
            for e in sorted(fb - fa):
                print('    ', e)

        self.assertEqual(0, errors)

    def test_parse_everything(self):
        import json
        from os.path import exists
        from metatab import TermParser, CsvPathRowGenerator

        for fn in ['example1.csv', 'example2.csv', 'example1-web.csv',
                   'include1.csv', 'include2.csv', 'include3.csv',
                   'children.csv', 'children2.csv',
                   'datapackage_ex1.csv', 'datapackage_ex1_web.csv', 'datapackage_ex2.csv',
                   'issue1.csv']:

            print('Testing ', fn);

            path = test_data(fn)

            json_path = test_data('json', fn.replace('.csv', '.json'))

            with open(path) as f:

                doc = MetatabDoc(terms=TermParser(CsvPathRowGenerator(path)))
                d = doc.as_dict()

                if not exists(json_path):
                    with open(json_path, 'w') as f:
                        json.dump(d, f, indent=4)

                with open(json_path) as f:
                    d2 = json.load(f)

                import json
                # print(json.dumps(doc._term_parser.declare_dict, indent=4))

                self.compare_dict(d, d2)

    def test_terms(self):
        from metatab import TermParser
        from metatab import CsvPathRowGenerator, CsvDataRowGenerator, RowGenerator
        import csv

        fn = test_data('example1.csv')

        with open(fn) as f:
            str_data = f.read();

        with open(fn) as f:
            row_data = [row for row in csv.reader(f)]

        for rg_args in ((CsvPathRowGenerator, fn),
                        (CsvDataRowGenerator, str_data, fn),
                        (RowGenerator, row_data, fn)):

            with open(fn) as f:
                rg = rg_args[0](*rg_args[1:])

                if False:
                    self.assertEqual(141, len(terms))

                    self.assertEqual('declare', terms[0].record_term)
                    self.assertEqual('metatab.csv', terms[0].value)

                    self.assertTrue(terms[48].file_name.endswith('example1.csv'))
                    self.assertEqual('root', terms[48].parent_term)
                    self.assertEqual('column', terms[48].record_term)
                    self.assertEqual('geoname', terms[48].value)

                    self.assertTrue(terms[100].file_name.endswith('example1.csv'))
                    self.assertEqual('root', terms[100].parent_term)
                    self.assertEqual('column', terms[100].record_term)
                    self.assertEqual('percent', terms[100].value)

                rg = rg_args[0](*rg_args[1:])

                doc = MetatabDoc(TermParser(rg))

                d = doc.as_dict()

                l1 = sorted(['creator', 'datafile', 'declare', 'description', 'documentation',
                             'format', 'homepage', 'identifier', 'note', 'obsoletes',
                             'spatial', 'spatialgrain', 'table', 'time', 'title',
                             'version', 'wrangler'])

                l2 = sorted(str(e) for e in d.keys())

                self.assertListEqual(l1,l2,"Failure for file '{}' ".format(fn))

    def test_declarations(self):

        from util import declaration_path

        fn = test_data('example1.csv')
        term_interp = TermParser(CsvPathRowGenerator(fn))
        _ = list(term_interp)

        d = { k:v for k,v in  term_interp.declare_dict['terms'].items() if 'homepage' in k}

        self.assertEqual(16, len(d))

        self.assertIn("homepage.mediatype", d.keys())
        self.assertIn("homepage.hash", d.keys())
        self.assertIn("homepage.title", d.keys())

        # Direct use of function

        ti = TermParser(CsvPathRowGenerator(declaration_path('metatab-latest')), False)
        ti.install_declare_terms()

        fn = test_data('example1.csv')  # Not acutally used. Sets base directory

        term_interp = TermParser(RowGenerator([['Declare', 'metatab']], fn))

        list(term_interp)  # Run the iterator

        d = term_interp.declare_dict

        self.assertEqual(sorted(['terms', 'sections']), sorted(d.keys()))

        terms = d['terms']

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(190, len(terms.keys()))

        sections = d['sections']

        self.assertEquals({'contacts', 'declaredterms', 'declaredsections', 'root', 'resources', 'schemas'},
                          set(sections.keys()))

        # Use the Declare term

        fn = test_data('example1.csv')
        term_interp = TermParser(CsvPathRowGenerator(fn))

        _ = term_interp.declare_dict

        self.assertEqual({'terms', 'sections'}, set(d.keys()))

        terms = d['terms']

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(190, len(terms.keys()))

        sections = d['sections']

        self.assertEquals({'contacts', 'declaredterms', 'declaredsections', 'root', 'resources', 'schemas'},
                          set(sections.keys()))

        self.assertEqual(['Email'], sections['contacts']['args'])
        self.assertEqual(['TermValueName', 'ChildPropertyType', 'Section'], sections['declaredterms']['args'])
        self.assertEqual(['DataType', 'ValueType', 'Description'], sections['schemas']['args'])

        #




    def test_children(self):

        fn = test_data('children.csv')

        doc = MetatabDoc(terms=TermParser(CsvPathRowGenerator(fn)))

        for t in doc.as_dict()['parent']:
            self.assertEquals({'prop1': 'prop1', 'prop2': 'prop2', '@value': 'parent'}, t)

    def test_includes(self):

        fn = test_data('include1.csv')

        doc = MetatabDoc(TermParser(CsvPathRowGenerator(fn)))
        d = doc.as_dict()

        self.assertEquals(['Include File 1', 'Include File 2', 'Include File 3'], d['note'])
        self.assertEquals(['/Volumes/Storage/proj/virt/ambry/metatab-py/test-data/include2.csv',
                           'https://raw.githubusercontent.com/CivicKnowledge/structured_tables/master/test/data/include3.csv'],
                          d['include'])

    def test_errors(self):

        def errs(fn):
            ti = TermParser(CsvPathRowGenerator(fn))
            with self.assertRaises(IncludeError):
                _ = list(ti)
            return ti.errors_as_dict()

        e = errs(test_data('errors/bad_include.csv'))

        self.assertEquals(1, len(e))
        self.assertTrue('bad_include.csv' in e[0]['file'])
        self.assertEquals('root.include', e[0]['term'])

        e = errs(test_data('errors/bad_declare.csv'))

        self.assertEquals(1, len(e))
        self.assertTrue('bad_declare.csv' in e[0]['file'])
        self.assertEquals('root.declare', e[0]['term'])

    def test_datapackage(self):
        from tempfile import NamedTemporaryFile
        import datapackage
        from os import unlink

        ti = TermParser(CsvPathRowGenerator(test_data('datapackage_ex2.csv')))

        doc = MetatabDoc(terms=ti)

        d = doc.as_dict()

        f = NamedTemporaryFile(delete=False)
        f.write(json.dumps(d, indent=4))
        f.close()

        try:
            dp = datapackage.DataPackage(f.name)
            dp.validate()
        except:
            with open(f.name) as f2:
                print(f2.read())
            raise

        unlink(f.name)

    def test_serializer(self):

        fn = test_data('schema.csv')

        doc = MetatabDoc(TermParser(CsvPathRowGenerator(fn)))
        d = doc.as_dict()

        s = Serializer()
        s.load_declarations(d)

        sections = defaultdict(list)

        for e in s.semiflatten(d):
            print(e)

        return

        for e in sorted(s.serialize(d)):
            has_int = any(isinstance(ki, int) for ki in e[0])
            key_no_int = tuple(ki for ki in e[0] if not isinstance(ki, int))
            print(key_no_int)
            pr = '.'.join(key_no_int[-2:])
            t = Term(pr, e[1], row=0, col=0, file_name=None)
            section = s.decl['terms'].get(t.join(), {}).get('section', 'Root')

            sections[section].append(t)

        return

        for k, v in sections.items():
            print("=====", k)
            for t in v:
                print(t)

    def test_headers(self):

        from metatab import TermParser, CsvPathRowGenerator

        d1 = TermParser(CsvPathRowGenerator(test_data('example1-headers.csv'))).root.as_dict()
        d2 = TermParser(CsvPathRowGenerator(test_data('example1.csv'))).root.as_dict()

        self.compare_dict(d1, d2)

    def test_find(self):

        ti = parse_file(test_data('example1.csv'))
        doc = MetatabDoc(terms=ti)

        self.assertEquals('cdph.ca.gov-hci-registered_voters-county', doc.find_first('Root.Identifier').value)

    def test_sections(self):

        from metatab import parse_file, MetatabDoc

        ti = parse_file(test_data('example1.csv'))

        doc = MetatabDoc(terms=ti)

        self.assertEqual(['root', u'resources', u'contacts', u'notes', u'schema'], doc.sections.keys())

        del doc['Resources']

        self.assertEqual(['root', u'contacts', u'notes', u'schema'], doc.sections.keys())

        notes = list(doc['notes'])

        self.assertEquals(2, len(notes))

        for sname, s in doc.sections.items():
            print(sname, s.value)


if __name__ == '__main__':
    unittest.main()
