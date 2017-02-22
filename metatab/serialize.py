# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Convert a data structure into a sequence of metatab rows
"""
import collections
from six import string_types
from .parser import TermParser
from .generate import MetatabRowGenerator

class Serializer(object):

    def __init__(self, config=None):
        """

        Initialize the serializer, possibly with a declaration file. If
        the declaration file is provided, it is used to determine what sections the
        resulting metatab file should have, what the arguments are for those sections, and
        what in what order those sections should appear.

        :param config: A reference to a metatab declare file
        :return: a sequence of rows of scalars
        """

        if config:

            term_interp = TermParser(MetatabRowGenerator([['Declare', config]], "<none>"))

            term_interp.run()

            self.decl = term_interp.declare_dict
        else:
            self.decl = {
                'sections': {},
                'terms': {},
            }

    def serialize(self, d):

        self.load_declarations(d)

        top_terms = []

        for k, v in d.items():
            if isinstance(v, collections.MutableMapping):
                top_terms.append( (k, v))
            elif isinstance(v, collections.MutableSequence):
                for e in v:
                    top_terms.append((k, e))
            else:
                top_terms.append((k, v))

        return top_terms

    def semiflatten(self, d, sep='.'):
        """Break a dict up into terms. This doens't really work, in general; it will
        only properly deal with two nested levels. At more than two levels"""

        def _flatten(e, parent_key):

            if isinstance(e, collections.MutableMapping):
                for k,v in e.items():
                    if not isinstance(v, string_types):
                        for i in _flatten(v, parent_key):
                            yield (k,i)
                        del e[k]
                yield e
            elif isinstance(e, collections.MutableSequence):
                for v in e:
                    for i in _flatten(v, parent_key):
                        yield i
            else:
                yield e

        for k,v in d.items():
            for e in _flatten(v,k):
                if isinstance(e, tuple):
                    yield (k+'.'+e[0], e[1])
                else:
                    yield (k, e)


    def load_declarations(self, d):

        def _load_declaration(dcl):

            term_interp = MetatabDoc(MetatabRowGenerator([['Declare', dcl]], "<none>"))

            _ = list(term_interp)

            return term_interp.declare_dict

        if 'declare' in d:

            decls = d['declare'] if isinstance(d['declare'], list) else [d['declare']]

            for dcl in decls:
                dd = _load_declaration(dcl)
                self.decl['terms'].update(dd['terms'])
                self.decl['sections'].update(dd['sections'])


