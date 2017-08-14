from __future__ import print_function

import json
import unittest

from metatab import IncludeError
from metatab import MetatabRowGenerator, TermParser, CsvPathRowGenerator, parse_file
from metatab.doc import MetatabDoc
from metatab.util import flatten, declaration_path
from metatab import TermParser, CsvPathRowGenerator, Serializer, Term
from collections import defaultdict
from metatab.doc import Resource
import csv
from os.path import dirname
from metatab.doc import open_package
import json
from os.path import exists
from metatab import parse_file, MetatabDoc

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

                #import json
                #print(json.dumps(d, indent=4))

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

        doc =  MetatabDoc(MetatabRowGenerator([['Declare', 'metatab-latest']], fn))

        terms = doc.decl_terms

        self.assertIn('root.homepage', terms.keys())
        self.assertIn('documentation.description', terms.keys())
        self.assertEquals(247, len(terms.keys()))

        sections = doc.decl_sections

        self.assertEquals({'contacts', 'declaredterms', 'declaredsections', 'root', 'resources', 'schemas',
                           'sources','documentation','data'},
                          set(sections.keys()))

        # Use the Declare term

        fn = test_data('example1.csv')
        doc = MetatabDoc(CsvPathRowGenerator(fn))

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
                tp = TermParser(CsvPathRowGenerator(fn), doc=doc)
                _ = list(tp)

            return tp.errors_as_dict()

        e = errs(test_data('errors/bad_include.csv'))

        print(e)

        self.assertEquals(1, len(e))
        self.assertTrue('bad_include.csv' in e[0]['file'])
        self.assertEquals('root.include', e[0]['term'])

        e = errs(test_data('errors/bad_declare.csv'))

        self.assertEquals(1, len(e))

        self.assertTrue('bad_declare.csv' in e[0]['error'])



    def test_serializer(self):

        return

        doc = MetatabDoc(test_data('schema.csv'))
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

        d1 = MetatabDoc(test_data('example1-headers.csv')).root.as_dict()
        d2 = MetatabDoc(test_data('example1.csv')).root.as_dict()

        self.compare_dict(d1, d2)

    def test_find(self):

        doc = MetatabDoc(test_data('example1.csv'))

        self.assertEquals('cdph.ca.gov-hci-registered_voters-county', doc.find_first('Root.Identifier').value)

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

    def test_generic_row_generation(self):
        from metatab import GenericRowGenerator

        url = 'gs://14_nfiTtSiMSjDes6BSiLU-Gsqy8DIdUxpMaH6DswcVQ'

        doc = MetatabDoc(url)

        self.assertEquals('Registered Voters, By County',doc.find_first('root.title').value)

        url = 'http://assets.metatab.org/examples/example-package.xls#meta'

        doc = MetatabDoc(url)

        self.assertEquals('17289303-73fa-437b-97da-2e1ed2cd01fd', doc.find_first('root.identifier').value)

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

        print( t.term, t.qualified_term, t.join)

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
        import datapackage
        from metatab.datapackage import convert_to_datapackage

        for fn in ('name.csv','name2.csv'):

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

        self.assertEquals(144, (len(list(doc.all_terms))))

    def test_resolved_url(self):


        with open(test_data('resolve_urls.csv')) as f:
            for row in csv.DictReader(f):
                doc = open_package(test_data(row['doc']))

                base = dirname(doc._ref)
                rs = doc['Resources']

                t = rs.new_term('Root.Datafile', row['resource_url'])
                t.term_value_name = 'url'

                if row['base_url']:
                    r = Resource(t, row['base_url'])
                else:
                    r = Resource(t, doc.package_url if doc.package_url else doc._ref)

                #print(r.resolved_url.replace(base, '<base>'), row['url'].replace("file:",''))
                self.assertEquals(r.resolved_url.replace(base, '<base>').replace('file:',''),
                                  row['url'].replace('file:',''))

    def test_versions(self):

        doc = MetatabDoc(test_data('example1.csv'))

        self.assertEqual('201404',doc.find_first_value('Root.Version'))
        self.assertEqual('201409',doc.as_version('+5').find_first_value('Root.Version'))
        self.assertEqual('201399',doc.as_version('-5').find_first_value('Root.Version'))
        self.assertEqual('foobar',doc.as_version('foobar').find_first_value('Root.Version'))


    def test_acessors(self):

        doc = MetatabDoc(test_data('civicknowledge.com-rcfe_affordability-2015.csv'))

        t = doc.find_first('Root.Reference')

        self.assertIn('name', t.properties)
        self.assertIn('url', t.properties)

        print([name for name, value in vars(t.__class__).items() if isinstance(value, property)])

        self.assertEqual(t.name,'B09020')
        self.assertEqual(t.url,'censusreporter:B09020/140/05000US06073')

        self.assertEqual(t.join,'root.reference')

        r = doc.reference(t.name)

        self.assertIn('name', r.properties)
        self.assertIn('url', r.properties)

        self.assertEqual(r.name,'B09020')
        self.assertEqual(r.url,'censusreporter:B09020/140/05000US06073')


if __name__ == '__main__':
    unittest.main()
