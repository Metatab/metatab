from __future__ import print_function

import json
import unittest
from appurl import parse_app_url
from metatab import IncludeError
from metatab.util import flatten, declaration_path
from metatab import TermParser
from metatab.terms import Term
from collections import defaultdict

import json
from os.path import exists
from metatab import MetatabDoc, WebResolver
from rowgenerators import get_generator


def test_data(*paths):
    from os.path import dirname, join, abspath

    return abspath(join(dirname(dirname(abspath(__file__))), 'test-data', *paths))


class MyTestCase(unittest.TestCase):
    def compare_dict(self, a, b):

        fa = set('{}={}'.format(k, v) for k, v in flatten(a));
        fb = set('{}={}'.format(k, v) for k, v in flatten(b));

        # The declare lines move around a lot, and rarely indicate an error
        fa = {e for e in fa if not e.startswith('declare=')}
        fb = {e for e in fb if not e.startswith('declare=')}

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

    def test_new_parser(self):

        tp = MetatabDoc(test_data('short.csv'))

        for t in tp.terms:
            print(t)

        import json
        print(json.dumps(tp.decl_terms, indent=4))

    def test_parse_everything(self):

        all = ['example1.csv', 'example2.csv', 'example1-web.csv',
               'include1.csv', 'include2.csv', 'include3.csv',
               'children.csv', 'children2.csv',
               'datapackage_ex1.csv', 'datapackage_ex1_web.csv', 'datapackage_ex2.csv',
               'issue1.csv']

        all = ['example1.csv']

        for fn in all:

            print('Testing ', fn);

            path = test_data(fn)

            json_path = test_data('json', fn.replace('.csv', '.json'))

            with open(path) as f:

                doc = MetatabDoc(path)
                d = doc.as_dict()

                if not exists(json_path):
                    with open(json_path, 'w') as f:
                        print("Writing", json_path)
                        json.dump(d, f, indent=4)

                with open(json_path) as f:
                    d2 = json.load(f)

                # import json
                # print(json.dumps(d, indent=4))

                self.compare_dict(d, d2)

    @unittest.skip('broken')
    def test_declarations(self):

        doc = MetatabDoc(test_data('example1.csv'))

        d = {k: v for k, v in doc.decl_terms.items() if 'homepage' in k}

        self.assertEqual(17, len(d))

        self.assertIn("homepage.mediatype", d.keys())
        self.assertIn("homepage.hash", d.keys())
        self.assertIn("homepage.title", d.keys())

        # Direct use of function

        ti = TermParser(CsvPathRowGenerator(declaration_path('metatab-latest')), False)
        ti.install_declare_terms()

        fn = test_data('example1.csv')  # Not acutally used. Sets base directory

        doc = MetatabDoc(MetatabRowGenerator([['Declare', 'metatab-latest']], fn))

        terms = doc.decl_terms

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(247, len(terms.keys()))

        sections = doc.decl_sections

        self.assertEquals({'contacts', 'declaredterms', 'declaredsections', 'root', 'resources', 'schemas',
                           'sources', 'documentation', 'data'},
                          set(sections.keys()))

        # Use the Declare term

        fn = test_data('example1.csv')
        doc = MetatabDoc(CsvPathRowGenerator(fn), resolver=WebResolver)

        d = doc._term_parser.declare_dict

        self.assertEqual({'terms', 'synonyms', 'sections'}, set(d.keys()))

        terms = d['terms']

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(247, len(terms.keys()))

        sections = d['sections']

        self.assertEquals({'contacts', 'declaredterms', 'declaredsections', 'root', 'resources', 'schemas',
                           'sources', 'documentation', 'data'},
                          set(sections.keys()))

        self.assertEqual(['Email', 'Organization', 'Tel', 'Url'], sections['contacts']['args'])
        self.assertEqual(['TermValueName', 'ChildPropertyType', 'Section'], sections['declaredterms']['args'])
        self.assertEqual(['DataType', 'ValueType', 'Description'], sections['schemas']['args'])

        #

    def test_children(self):

        doc = MetatabDoc(test_data('children.csv'))

        for t in doc.terms:
            print(t)

        import json
        print(json.dumps(doc.as_dict(), indent=4))

        for t in doc.as_dict()['parent']:
            self.assertEquals({'prop1': 'prop1', 'prop2': 'prop2', '@value': 'parent'}, t)

    def test_includes(self):

        doc = MetatabDoc(test_data('include1.csv'))
        d = doc.as_dict()

        for t in doc['root'].terms:
            print(t)

        print(d)

        self.assertEquals(['Include File 1', 'Include File 2', 'Include File 3'], d['note'])

        self.assertTrue(any('include2.csv' in e for e in d['include']))
        self.assertTrue(any('include3.csv' in e for e in d['include']))

    def test_errors(self):

        def errs(fn):
            with self.assertRaises(IncludeError):
                doc = MetatabDoc()
                tp = TermParser(fn, resolver=WebResolver, doc=doc)
                _ = list(tp)

            return tp.errors_as_dict()

        e = errs(parse_app_url(test_data('errors/bad_include.csv')))

        print(e)

        self.assertEquals(1, len(e))
        self.assertTrue('bad_include.csv' in e[0]['file'])
        self.assertEquals('root.include', e[0]['term'])

        e = errs(test_data('errors/bad_declare.csv'))

        self.assertEquals(1, len(e))

        self.assertTrue('bad_declare.csv' in e[0]['error'])



    def test_headers(self):
        d1 = MetatabDoc(test_data('example1-headers.csv')).root.as_dict()
        d2 = MetatabDoc(test_data('example1.csv')).root.as_dict()

        self.compare_dict(d1, d2)

    def test_find(self):

        doc = MetatabDoc(test_data('example1.csv'))

        self.assertEquals('cdph.ca.gov-hci-registered_voters-county', doc.find_first('Root.Identifier').value)

        doc = MetatabDoc(test_data('resources.csv'))

        self.assertEqual({'root.downloadpage', 'root.supplementarydata', 'root.api', 'root.citation',
                          'root.datafile', 'root.datadictionary', 'root.image', 'root.reference',
                          'root.documentation', 'root.homepage'},
                         doc.derived_terms['root.resource'])

        self.assertEqual(['example1', 'example10', 'example2', 'example3', 'example4', 'example5', 'example6',
                'example7', 'example8', 'example9'], sorted([t.name for t in doc.find('root.resource')]))

        self.assertEquals(['example1', 'example2'], [t.name for t in doc.find('root.datafile')])

    def test_sections(self):

        doc = MetatabDoc(test_data('example1.csv'))

        self.assertEqual(['root', u'resources', u'contacts', u'notes', u'schema'],
                         list(doc.sections.keys()))

        del doc['Resources']

        self.assertEqual(['root', u'contacts', u'notes', u'schema'], list(doc.sections.keys()))

        notes = list(doc['notes'])

        self.assertEquals(2, len(notes))

        for sname, s in doc.sections.items():
            print(sname, s.value)

    @unittest.skip('datapackage-1.0.0a2 seems to be missing a file')
    def test_datapackage_declare(self):
        from tempfile import NamedTemporaryFile
        import datapackage
        from os import unlink

        doc = MetatabDoc(test_data('datapackage_ex2.csv'))

        d = doc.as_dict()

        f = open('/tmp/package.json', 'w')  # NamedTemporaryFile(delete=False)
        f.write(json.dumps(d, indent=4))
        f.close()

        try:
            dp = datapackage.DataPackage(f.name)
            dp.validate()
        except:
            with open(f.name) as f2:
                print(f2.read())
            raise

        print(f.name)
        # unlink(f.name)

        doc = MetatabDoc(test_data('example1.csv'))

        from metatab.datapackage import convert_to_datapackage

        print(json.dumps(convert_to_datapackage(doc), indent=4))

    @unittest.skip('datapackage-1.0.0a2 seems to be missing a file')
    def test_datapackage_convert(self):
        import datapackage
        from metatab.datapackage import convert_to_datapackage

        doc = MetatabDoc(test_data('example1.csv'))

        dp = convert_to_datapackage(doc)

        print(json.dumps(dp, indent=4))

        dp = datapackage.DataPackage(dp)
        dp.validate()

    def test_change_term(self):

        p = Term('parent', 'value')

        t = Term('Parent.Child', 'value', parent=p)

        print(t.term, t.qualified_term, t.join)

        self.assertEquals('Parent.Child', t.term)
        self.assertEquals('parent.child', t.qualified_term)
        self.assertEquals('parent.child', t.join)

        t.term = 'Parent2.Child2'

        print(t.term, t.qualified_term, t.join)

        self.assertEquals('Parent2.Child2', t.term)
        self.assertEquals('parent.child2', t.qualified_term)
        self.assertEquals('parent2.child2', t.join)

        t.parent = None
        t.term = 'Parent3'

        print(t.term, t.qualified_term, t.join)

        self.assertEquals('Parent3', t.term)
        self.assertEquals('root.parent3', t.qualified_term)
        self.assertEquals('root.parent3', t.join)

    def test_update_name(self):

        for fn in ('name.csv', 'name2.csv'):

            doc = MetatabDoc(test_data(fn))

            updates = doc.update_name()

            name = doc.find_first_value("Root.Name")

            self.assertEquals('example.com-foobar-2017-ca-people-1', name)
            self.assertEquals(['Changed Name'], updates)

            try:
                doc.remove_term(doc.find_first('Root.Dataset'))
            except ValueError:
                nv = doc.find_first('Root.Name')
                nv.remove_child(nv.find_first('Name.Dataset'))

            updates = doc.update_name()

            self.assertIn("No Root.Dataset, so can't update the name", updates)

    def test_descendents(self):

        doc = MetatabDoc(test_data('example1.csv'))

        self.assertEquals(146, (len(list(doc.all_terms))))

    def test_versions(self):

        doc = MetatabDoc(test_data('example1.csv'))

        self.assertEqual('201404', doc.find_first_value('Root.Version'))
        self.assertEqual('example.com-voters-2002_2014-ca-county-201409', doc.as_version('+5'))
        self.assertEqual('example.com-voters-2002_2014-ca-county-201399', doc.as_version('-5'))
        self.assertEqual('example.com-voters-2002_2014-ca-county-foobar', doc.as_version('foobar'))
        self.assertEqual('example.com-voters-2002_2014-ca-county', doc.as_version(None))

    def test_acessors(self):

        doc = MetatabDoc(test_data('properties.csv'))

        c = doc.find_first('Root.Citation', name='ipums')

        # Arg_props not include Author, Title or Year, which are children, but not arg props
        self.assertEquals(['type', 'month', 'publisher', 'journal', 'version', 'volume',
                           'number', 'pages', 'accessdate', 'location', 'url', 'doi', 'issn', 'name'],
                          list(c.arg_props.keys()))

        # Props includes just the children that actually have values
        self.assertEquals(['type', 'publisher', 'version', 'accessdate', 'url', 'doi', 'author', 'title', 'year'],
                          list(c.props.keys()))

        # All props includes values for all of the children and all of the property args
        self.assertEquals(['type', 'month', 'publisher', 'journal', 'version', 'volume',
                           'number', 'pages', 'accessdate', 'location', 'url', 'doi', 'issn', 'name', 'author', 'title',
                           'year'],
                          list(c.all_props.keys()))

        # Attribute acessors
        self.assertEqual('dataset', c.type)
        self.assertEqual('2017', c.year)
        self.assertEqual('Integrated Public Use Microdata Series', c.title)
        self.assertEqual('University of Minnesota', c.publisher)

        # These are properties of Term
        self.assertEqual(c.join, 'root.citation')
        self.assertTrue(c.term_is('Root.Citation'))

        # Item style acessors
        self.assertEqual('dataset', c['type'].value)
        self.assertTrue(c['type'].term_is('Citation.Type'))
        self.assertEqual('2017', c['year'].value)
        self.assertEqual('Integrated Public Use Microdata Series', c['title'].value)
        self.assertEqual('University of Minnesota', c['publisher'].value)
        self.assertTrue(c['publisher'].term_is('Citation.Publisher'))

        c.foo = 'bar'

        c.type = 'foobar'
        self.assertEqual('foobar', c.type)
        self.assertEqual('foobar', c['type'].value)


    def test_term_subclasses(self):
        from metatab.terms import Term, SectionTerm
        from metatab import WebResolver

        doc = MetatabDoc()
        tp = TermParser(test_data('example1.csv'), resolver=WebResolver, doc=doc)

        terms = list(tp)

        self.assertEqual(Term, tp.get_term_class('root.summary'))
        self.assertEqual(Term, tp.get_term_class('root.name'))
        self.assertEqual(SectionTerm, tp.get_term_class('root.section'))
        #self.assertEqual(Resource, tp.get_term_class('root.resource'))
        #self.assertEqual(Resource, tp.get_term_class('root.homepage'))

        class TestTermClass(Term):
            pass

        TermParser.register_term_class('root.name', TestTermClass)

        self.assertEqual(TestTermClass, tp.get_term_class('root.name'))

        doc = MetatabDoc(test_data('example1.csv'))

        self.assertEqual(Term, type(doc.find_first('root.description')))
        self.assertEqual(TestTermClass, type(doc.find_first('root.name')))
        
        #self.assertEqual(Resource, type(doc.find_first('root.datafile')))
        #self.assertEqual(Resource, type(doc.find_first('root.homepage')))

if __name__ == '__main__':
    unittest.main()
