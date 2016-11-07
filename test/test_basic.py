from __future__ import print_function
import unittest

import collections
import json
from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator, Serializer


def flatten(d, sep='.'):

    def _flatten(e, parent_key='', sep='.'):
        import collections

        prefix = parent_key+sep if parent_key else ''

        if isinstance(e, collections.MutableMapping):
            return tuple( (prefix+k2, v2) for k, v in e.items() for k2,v2 in _flatten(v,  k, sep ) )
        elif isinstance(e, collections.MutableSequence):
            return tuple( (prefix+k2, v2) for i, v in enumerate(e) for k2,v2 in _flatten(v,  str(i), sep ) )
        else:
            return (parent_key, (e,)),

    return tuple( (k, v[0]) for k, v in _flatten(d, '', sep) )

def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class MyTestCase(unittest.TestCase):

    def compare_dict(self, a, b):
        fa = set('{}={}'.format(k, v) for k, v in flatten(a));
        fb = set('{}={}'.format(k, v) for k, v in flatten(b));

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
        from os.path import dirname, join, exists
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator

        for fn in ['example1.csv', 'example2.csv', 'example1-web.csv',
                   'include1.csv', 'include2.csv', 'include3.csv',
                   'children.csv', 'children2.csv',
                   'datapackage_ex1.csv', 'datapackage_ex1_web.csv', 'datapackage_ex2.csv',
                   'issue1.csv']:

            print('Testing ', fn);

            path = test_data(fn)

            json_path = test_data('json', fn.replace('.csv', '.json'))

            with open(path) as f:
                term_gen = list(TermGenerator(CsvPathRowGenerator(path)))

                term_interp = TermInterpreter(term_gen)

                d = term_interp.as_dict()

                if not exists(json_path):
                    with open(json_path, 'w') as f:
                        json.dump(d, f, indent=4)

                with open(json_path) as f:
                    d2 = json.load(f)

                self.compare_dict(d, d2)



    def test_terms(self):
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter
        from metatab import CsvPathRowGenerator, CsvDataRowGenerator, RowGenerator
        import csv
        import json

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

                print(rg.__class__.__name__)

                terms = list(TermGenerator(rg))

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

                terms = TermInterpreter(TermGenerator(rg))

                d = terms.as_dict()

                self.assertListEqual(sorted(['creator', 'datafile', 'declare', 'description', 'documentation',
                                             'format', 'homepage', 'identifier', 'note', 'obsoletes',
                                             'spatial', 'spatialgrain', 'table', 'time', 'title',
                                             'version', 'wrangler']),
                                     sorted(d.keys()))

    def test_declarations(self):
        from os.path import dirname, join
        from metatab import CsvPathRowGenerator, RowGenerator, TermGenerator, TermInterpreter, Term

        import csv, json

        # Direct use of function

        ti = TermInterpreter(TermGenerator(CsvPathRowGenerator(test_data('metatab.csv'))), False)
        ti.install_declare_terms()

        fn = test_data('example1.csv')  # Not acutally used. Sets base directory

        term_interp = TermInterpreter(TermGenerator(RowGenerator([['Declare', 'metatab.csv']], fn)))

        term_interp.run()

        d = term_interp.declare_dict

        self.assertEqual(sorted(['terms', 'sections']), sorted(d.keys()))

        terms = d['terms']

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(46, len(terms.keys()))

        sections = d['sections']

        self.assertEquals({'contacts', 'declaredterms', 'declaredsections', 'root', 'resources', 'schema'},
                          set(sections.keys()))

        # Use the Declare term

        fn = test_data('example1.csv')
        term_interp = TermInterpreter(TermGenerator(CsvPathRowGenerator(fn)))

        _ = term_interp.declare_dict

        self.assertEqual({'terms', 'sections'}, set(d.keys()))

        terms = d['terms']

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(46, len(terms.keys()))

        sections = d['sections']

        self.assertEquals({'contacts', 'declaredterms', 'declaredsections', 'root', 'resources', 'schema'},
                          set(sections.keys()))

    def test_children(self):
        import json

        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator
        fn = test_data('children.csv')

        term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp = TermInterpreter(term_gen)

        for t in term_interp.as_dict()['parent']:
            self.assertEquals({'prop1': 'prop1', 'prop2': 'prop2', '@value': 'parent'}, t)

    def test_includes(self):
        import json
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator

        fn = test_data('include1.csv')

        term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp = TermInterpreter(term_gen)

        d = term_interp.as_dict()

        self.assertEquals(['Include File 1', 'Include File 2', 'Include File 3'], d['note'])
        self.assertEquals(['/Volumes/Storage/proj/virt/metatab/metatab-py/test-data/include2.csv',
                           'https://raw.githubusercontent.com/CivicKnowledge/structured_tables/master/test/data/include3.csv'],
                          d['include'])

    def test_errors(self):

        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator, IncludeError

        def errs(fn):
            ti = TermInterpreter(TermGenerator(CsvPathRowGenerator(fn)))
            with self.assertRaises(IncludeError):
                ti.run()
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

        d = TermInterpreter(TermGenerator(CsvPathRowGenerator(test_data('datapackage_ex2.csv')))).as_dict()

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

    def test_section_dict(self):

        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator

        fn = test_data('example1.csv')

        term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp = TermInterpreter(term_gen)

        d = term_interp.as_section_dict();

        keys = ( ('notes',2), ('schema',1), ('root',10), ('resources',4), ('contacts',2) )

        self.assertEquals([ key for key,_ in keys], d.keys());

        for key, size in keys:
            self.assertEqual(size, len(d[key]), "'{}' key in section dict".format(key))

    def test_serializer(self):

        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator, Serializer, Term
        from collections import defaultdict

        fn = test_data('schema.csv')

        term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp = TermInterpreter(term_gen)

        d = term_interp.as_dict()

        s = Serializer()
        s.load_declarations(d)

        sections = defaultdict(list)

        for e in s.semiflatten(d):
            print(e)

        return

        for e in sorted(s.serialize(d)):
            has_int = any(isinstance(ki, int) for ki in e[0])
            key_no_int = tuple( ki for ki in e[0] if not isinstance(ki, int))
            print(key_no_int)
            pr = '.'.join(key_no_int[-2:])
            t = Term(pr, e[1], row=0, col=0, file_name=None)
            section = s.decl['terms'].get(t.join(), {}).get('section','Root')

            sections[section].append(t)

        return

        for k, v in sections.items():
            print("=====", k)
            for t in v:
                print (t)

    def test_headers(self):

        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator, Serializer
        import json

        d1 = TermInterpreter(TermGenerator(CsvPathRowGenerator(test_data('example1-headers.csv')))).as_dict()
        d2 = TermInterpreter(TermGenerator(CsvPathRowGenerator(test_data('example1.csv')))).as_dict()

        self.compare_dict(d1, d2)

        #import json
        #print(json.dumps(d1, indent=4))

if __name__ == '__main__':
    unittest.main()
