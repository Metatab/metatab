

import warnings
warnings.simplefilter('ignore')

import unittest


class TestCreate(unittest.TestCase):


    def x_test_basic(self):

        from metapack.support import metapack_defaults_file
        from metapack import MetapackDoc

        d = MetapackDoc(metapack_defaults_file())

        d['Root'].set_terms(
            Title='This is the title',
            Description='Description!',
            Origin='busboom.org',
            Dataset='foobar')

        d['Contacts'].set_terms(
            Wrangler=('Eric Busboom', {'Email':'eric@busboom.org', 'Url':'http://busboom.org'})
        )

        d.sort_by_term()
        d.update_name()

        print(d.as_lines())



if __name__ == '__main__':
    unittest.main()
