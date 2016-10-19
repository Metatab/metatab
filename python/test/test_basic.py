import unittest



class MyTestCase(unittest.TestCase):

    def test_web(self):
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator
        fn = join(dirname(__file__), 'data', 'example1-web.csv')

        with open(fn) as f:
            term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

            term_interp = TermInterpreter(term_gen)

            print term_interp.as_dict().keys()

            print term_interp.errors_as_dict()

    def test_children(self):
        import json
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator
        fn = join(dirname(__file__), 'data', 'children.csv')


        term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp = TermInterpreter(term_gen)

        for t in term_interp.as_dict()['parent']:
            self.assertEquals({'prop1': 'prop1', 'prop2': 'prop2', '@value': 'parent'}, t)


    def test_includes(self):
        import json
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator

        fn = join(dirname(__file__), 'data', 'include1.csv')

        term_gen = list(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp = TermInterpreter(term_gen)

        d = term_interp.as_dict()

        self.assertEquals(['Include File 1', 'Include File 2', 'Include File 3'], d['note'])
        self.assertEquals(['include2.csv',
                           'https://raw.githubusercontent.com/CivicKnowledge/structured_tables/master/test/data/include3.csv'],
                          d['include'])


    def test_parse_everything(self):
        import json
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter, CsvPathRowGenerator

        for fn in ['example1.csv','example2.csv','example1-web.csv',
                  'include1.csv','include2.csv', 'include3.csv' ]:

            path = join(dirname(__file__), 'data', fn)

            with open(path) as f:
                term_gen = list(TermGenerator(CsvPathRowGenerator(path)))

                term_interp = TermInterpreter(term_gen)

                d = term_interp.as_dict()

                print fn, len(d)

    def test_terms(self):
        from os.path import dirname, join
        from metatab import TermGenerator, TermInterpreter
        from metatab import CsvPathRowGenerator, CsvDataRowGenerator, RowGenerator
        import csv
        import json

        fn = join(dirname(__file__), 'data', 'example1.csv')

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

                #for i, t in enumerate(terms):
                #    print i, t

                self.assertEqual(141, len(terms))

                self.assertEqual('declare', terms[0].record_term)
                self.assertEqual('metadata.csv', terms[0].value)

                self.assertTrue(terms[48].file_name.endswith('example1.csv'))
                self.assertEqual('<no_term>', terms[48].parent_term)
                self.assertEqual('column', terms[48].record_term)
                self.assertEqual('geoname', terms[48].value)

                self.assertTrue(terms[100].file_name.endswith('example1.csv'))
                self.assertEqual('<no_term>', terms[100].parent_term)
                self.assertEqual('column', terms[100].record_term)
                self.assertEqual('percent', terms[100].value)

                rg = rg_args[0](*rg_args[1:])

                terms = TermInterpreter(TermGenerator(rg))

                self.assertListEqual(['creator', 'datafile', 'description', 'documentation', 'format', 'homepage',
                                      'identifier', 'note', 'obsoletes', 'spatial', 'spatialgrain', 'table',
                                      'time', 'title', 'version', 'wrangler'],
                                     sorted(terms.as_dict().keys()) )

    def test_declarations(self):
        from os.path import dirname, join
        from metatab import CsvPathRowGenerator, TermGenerator, TermInterpreter, Term

        import csv, json

        # Direct use of function

        fn = join(dirname(__file__), 'data', 'example1.csv') # Not acutally used. Sets base directory

        term_interp = TermInterpreter(TermGenerator(CsvPathRowGenerator(fn)))

        term_interp.handle_declare(Term('Declare','metadata.csv', file_name=fn))

        d = term_interp.declare_dict

        self.assertEqual(['terms', 'sections'], d.keys())

        terms = d['terms']

        self.assertIn('<no_term>.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(46, len(terms.keys()))

        sections = d['sections']

        self.assertEquals(['contacts', 'declaredsections', 'declaredterms', 'root', 'resources', 'schema'],
                          sections.keys())

        # Use the Declare term

        fn = join(dirname(__file__), 'data', 'example1.csv')
        term_interp = TermInterpreter(TermGenerator(CsvPathRowGenerator(fn)))

        _ = term_interp.declare_dict

        self.assertEqual(['terms', 'sections'], d.keys())

        terms = d['terms']

        self.assertIn('<no_term>.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(46, len(terms.keys()))

        sections = d['sections']

        self.assertEquals(['contacts', 'declaredsections', 'declaredterms', 'root', 'resources', 'schema'],
                          sections.keys())


if __name__ == '__main__':
    unittest.main()