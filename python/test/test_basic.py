import unittest


import collections

# From http://stackoverflow.com/a/6027615
def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)

def test_data(*paths):
    from os.path import dirname, join

    return join(dirname(dirname(dirname(__file__))), 'test-data',  *paths)


class MyTestCase(unittest.TestCase):

    def test_web(self):
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator
        fn = test_data('example1-web.csv')

        with open(fn) as f:
            term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

            term_interp = TermInterpreter(term_gen)

            print term_interp.as_dict().keys()

            print term_interp.errors_as_dict()

    def test_delcare_doc(self):
        import json
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator
        fn = test_data('declare-only.csv')

        term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp = TermInterpreter(term_gen)

        for t in term_interp:
            print t

        print json.dumps(term_interp.as_dict(), indent=4)

    def test_root(self):
        import json
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator
        fn = test_data('children.csv')

        term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp = TermInterpreter(term_gen)

        for t in term_interp:
            print t

        print json.dumps(term_interp.as_dict(),indent=4)

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
        self.assertEquals(['include2.csv',
                           'https://raw.githubusercontent.com/CivicKnowledge/structured_tables/master/test/data/include3.csv'],
                          d['include'])

    def test_parse_everything(self):
        import json
        from os.path import dirname, join, exists
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator

        for fn in ['example1.csv','example2.csv','example1-web.csv',
                   'include1.csv','include2.csv', 'include3.csv',
                   'children.csv','children2.csv']:

            path = test_data(fn)

            json_path = test_data('json',fn.replace('.csv', '.json'))

            with open(path) as f:
                term_gen = list(TermGenerator(CsvPathRowGenerator(path)))

                term_interp = TermInterpreter(term_gen)

                d = term_interp.as_dict()

                if not exists(json_path):
                    with open(json_path,'w') as f:
                        json.dump(d,f, indent=4)

                with open(json_path) as f:
                    d2 = json.load(f)

                self.assertDictEqual(flatten(d), flatten(d2));

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

        for rg_args in ( (CsvPathRowGenerator,fn),
                    (CsvDataRowGenerator,str_data, fn),
                    (RowGenerator,row_data, fn) ):

            with open(fn) as f:

                rg = rg_args[0](*rg_args[1:])

                print rg.__class__.__name__

                terms = list(TermGenerator(rg))


                self.assertEqual(141, len(terms))

                self.assertEqual('declare', terms[0].record_term)
                self.assertEqual('metadata.csv', terms[0].value)

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
                                             'format', 'homepage','identifier', 'note', 'obsoletes',
                                             'spatial', 'spatialgrain', 'table', 'time', 'title',
                                             'version', 'wrangler']),
                                     sorted(d.keys()) )

    def test_declarations(self):
        from os.path import dirname, join
        from metatab import CsvPathRowGenerator, RowGenerator, TermGenerator, TermInterpreter, Term

        import csv, json

        # Direct use of function

        ti = TermInterpreter(TermGenerator(CsvPathRowGenerator(test_data('metadata.csv'))), False)
        ti.install_declare_terms()

        fn = test_data('example1.csv') # Not acutally used. Sets base directory

        term_interp = TermInterpreter(TermGenerator(RowGenerator([['Declare','metadata.csv']], fn)))

        d = term_interp.declare_dict

        self.assertEqual(['terms', 'sections'], d.keys())

        terms = d['terms']

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(46, len(terms.keys()))

        sections = d['sections']

        self.assertEquals(['contacts', 'declaredterms', 'declaredsections', 'root', 'resources', 'schema'],
                          sections.keys())

        # Use the Declare term

        fn = test_data('example1.csv')
        term_interp = TermInterpreter(TermGenerator(CsvPathRowGenerator(fn)))

        _ = term_interp.declare_dict

        self.assertEqual(['terms', 'sections'], d.keys())

        terms = d['terms']

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(46, len(terms.keys()))

        sections = d['sections']

        self.assertEquals(['contacts','declaredterms', 'declaredsections',  'root', 'resources', 'schema'],
                          sections.keys())


if __name__ == '__main__':
    unittest.main()