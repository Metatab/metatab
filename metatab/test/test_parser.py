from __future__ import print_function

import json
import unittest
from os.path import exists


from metatab import IncludeError, MetatabDoc, WebResolver, TermParser
from metatab.terms import Term
from metatab.test.core import test_data
from metatab.util import flatten, declaration_path
from metatab.rowgenerators import TextRowGenerator
from rowgenerators import parse_app_url


class TestParser(unittest.TestCase):

    def setUp(self):
        import warnings
        warnings.simplefilter('ignore')

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

        import json

        all = ['example1.csv', 'example2.csv', 'example1-web.csv',
               'include1.csv', 'include2.csv', 'include3.csv',
               'children.csv', 'children2.csv',
               'issue1.csv'
               ]

        # These are currently broken -- as_dict doesn't work properly with the
        # datapackage-latest decl.
        datapackages = ['datapackage_ex1.csv', 'datapackage_ex1_web.csv', 'datapackage_ex2.csv']

        for fn in all:

            print('Testing ', fn);

            path = test_data(fn)

            json_path = test_data('json', fn.replace('.csv', '.json'))

            doc = MetatabDoc(path)
            d = doc.as_dict()


            if not exists(json_path):
                with open(json_path, 'w') as f:
                    print("Writing", json_path)
                    json.dump(d, f, indent=4)

            with open(json_path) as f:
                d2 = json.load(f)

            self.compare_dict(d, d2)


    def test_write_line_doc(self):
        """Convert CSV files to text lines and back to text lines"""

        all = ['example1.csv', 'example2.csv', 'example1-web.csv',
               'children.csv', 'children2.csv', 'issue1.csv' ]

        self.maxDiff = None

        for f in all:

            path = test_data(f)

            doc1 = MetatabDoc(path)

            doc1_lines = doc1.as_lines()

            print(doc1_lines)

            doc2 = MetatabDoc(TextRowGenerator(doc1_lines))

            doc2_lines = doc2.as_lines()

            self.assertEqual(doc1_lines, doc2_lines)

            self.compare_dict(doc1.as_dict(),doc2.as_dict())

            self.assertEqual(doc1_lines, doc2_lines)

            self.assertEqual(doc1.as_csv(), doc2.as_csv())


    def test_line_doc(self):

        doc = MetatabDoc(TextRowGenerator("Declare: metatab-latest"))

        with open(test_data('line/line-oriented-doc.txt')) as f:
            text = f.read()

        tp = TermParser(TextRowGenerator(text), resolver=doc.resolver, doc=doc)

        doc.load_terms(tp)

        self.assertEqual('47bc1089-7584-41f0-b804-602ec42f1249', doc.get_value('Root.Identifier'))
        self.assertEqual(150, len(doc.terms))

        self.assertEqual(5, len(list(doc['References'])))

        self.assertEqual(5, len(list(doc['References'].find('Root.Reference'))))

        self.assertEqual(5, len(list(doc['References'].find('Root.Resource')))) #References are Resources

        rt = list(doc['References'].find('Root.Resource'))[0]

        print(type(rt))

    def test_line_doc_parts(self):

        doc = MetatabDoc(TextRowGenerator("Declare: metatab-latest"))

        for fn in ('line/line-oriented-doc-root.txt',
                   'line/line-oriented-doc-contacts.txt',
                   'line/line-oriented-doc-references-1.txt',
                   'line/line-oriented-doc-references-2.txt',
                   'line/line-oriented-doc-bib.txt',
                  ):

            with open(test_data(fn)) as f:
                text = f.read()

            tp = TermParser(TextRowGenerator(text), resolver=doc.resolver, doc=doc)

            doc.load_terms(tp)

        self.assertEqual('47bc1089-7584-41f0-b804-602ec42f1249', doc.get_value('Root.Identifier'))
        self.assertEqual(150, len(doc.terms))

        self.assertEqual(5, len(list(doc['References'])))

        self.assertEqual(5,len(list(doc['References'].find('Root.Resource'))))


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

    @unittest.skip('Loads of trouble with this test. ')
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
                          'root.documentation', 'root.homepage', 'root.webpage','root.sql', 'root.dsn'},
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
        import datapackage

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
        self.assertEquals(sorted(['type', 'month', 'publisher', 'journal', 'version', 'volume',
                           'number', 'pages', 'accessdate', 'location', 'url', 'doi', 'issn', 'name']),
                          sorted(list(c.arg_props.keys())))

        # Props includes just the children that actually have values
        self.assertEquals(sorted(['type', 'publisher', 'version', 'accessdate', 'url', 'doi', 'author', 'title', 'year']),
                          sorted(list(c.props.keys())))

        # All props includes values for all of the children and all of the property args
        self.assertEquals(sorted(['type', 'month', 'publisher', 'journal', 'version', 'volume',
                           'number', 'pages', 'accessdate', 'location', 'url', 'doi', 'issn', 'name', 'author', 'title',
                           'year']),
                          sorted(list(c.all_props.keys())))

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

        try:
            TermParser.register_term_class('root.name', TestTermClass)

            self.assertEqual(TestTermClass, tp.get_term_class('root.name'))

            doc = MetatabDoc(test_data('example1.csv'))

            self.assertEqual(Term, type(doc.find_first('root.description')))
            self.assertEqual(TestTermClass, type(doc.find_first('root.name')))

            #self.assertEqual(Resource, type(doc.find_first('root.datafile')))
            #self.assertEqual(Resource, type(doc.find_first('root.homepage')))

        finally:
            # Some test environments seem to run test multipel times in the same interpreter,
            # and if we leave this registration active the test for 'root.name' above will fail.
            TermParser.unregister_term_class('root.name')

    def test_url(self):

        u = parse_app_url('metatab+file:///tmp/foobar.csv')

        self.assertEqual('metatab', u.proto)

        print(u)
        print(u.get_resource())
        print(u.get_resource().get_target())

if __name__ == '__main__':
    unittest.main()
