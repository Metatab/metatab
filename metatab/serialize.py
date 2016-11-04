# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Convert a data structure into a sequence of metatab rows
"""

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
            from parser import TermInterpreter, TermGenerator
            from generate import RowGenerator
            term_interp = TermInterpreter(TermGenerator(RowGenerator([['Declare', config]], "<none>")))

            term_interp.run()

            self.decl = term_interp.declare_dict
        else:
            self.decl = {
                'sections': {},
                'terms': {},
            }

    def serialize(self, d):

        self.load_declarations(d)

        #for t in self.decl['terms'].items():
        #    print t

        return self.flatten(d)

    def load_declarations(self, d):

        def _load_declaration(dcl):
            from parser import TermInterpreter, TermGenerator
            from generate import RowGenerator
            term_interp = TermInterpreter(TermGenerator(RowGenerator([['Declare', dcl]], "<none>")))

            term_interp.run()

            return term_interp.declare_dict

        if 'declare' in d:

            decls = d['declare'] if isinstance(d['declare'], list) else [d['declare']]

            for dcl in decls:
                dd = _load_declaration(dcl)
                self.decl['terms'].update(dd['terms'])
                self.decl['sections'].update(dd['sections'])

    def flatten(self, d, sep=None):

        def _flatten(e, parent_key):
            import collections

            if isinstance(e, collections.MutableMapping):
                return tuple((parent_key + k2, v2) for k, v in e.items() for k2, v2 in _flatten(v, (k,)))
            elif isinstance(e, collections.MutableSequence):
                return tuple((parent_key + k2, v2) for i, v in enumerate(e) for k2, v2 in _flatten(v, (i,)))
            else:
                return (parent_key, (e,)),

        return tuple((k if sep is None else sep.join(str(e) for e in k), v[0])
                     for k, v in _flatten(d, tuple()))

