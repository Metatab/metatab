

import warnings
warnings.simplefilter('ignore')

import json
import unittest
from os.path import exists

from metapack import MetapackDoc
from metatab import IncludeError, MetatabDoc, WebResolver, TermParser
from metatab.terms import Term
from metatab.test.core import test_data
from metatab.util import flatten, declaration_path
from metatab.generate import TextRowGenerator
from rowgenerators import parse_app_url


class TestCreate(unittest.TestCase):


    def test_basic(self):

        from metapack.support import metapack_defaults_file

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
