

# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Classes to build a Metatab document
"""


class MetatabDoc(object):
    def __init__(self, decl=None):

        import collections

        self.decl_terms = {}
        self.decl_sections = {}

        self.sections = collections.OrderedDict()

        if decl:

            if not isinstance(decl, collections.MutableSequence):
                decl = [decl]

            for d in decl:
                dd = self.load_declaration(d)

                self.decl_terms.update(dd['terms'])
                self.decl_sections.update(dd['sections'])

    def load_declaration(self, dcl):
        from metatab import TermInterpreter, TermGenerator
        from metatab import RowGenerator
        term_interp = TermInterpreter(TermGenerator(RowGenerator([['Declare', dcl]], "<none>")))
        term_interp.run()
        dd = term_interp.declare_dict

        self.decl_terms.update(dd['terms'])
        self.decl_sections.update(dd['sections'])

        return dd

    def new_section(self, name, params=None):
        """Return a new section"""
        self.sections[name] = Section(name, self, params)

        return self.sections[name]

    def get_or_new_section(self, name, params=None):
        """Create a new section or return an existing one of the same name"""
        if name not in self.sections:
            self.sections[name] = Section(name, self, params)

        return self.sections[name]

    @property
    def rows(self):
        """Iterate over all of the rows"""

        for s_name, s in self.sections.items():

            if s.name != 'Root':
                yield ['']
                yield ['Section', s.name] + s.param_names
            for row in s.rows:
                term, value = row

                term = term.replace('root.', '').title()

                try:
                    yield [term] + value
                except:
                    yield [term] + [value]

    def write_csv(self, path):
        import unicodecsv as csv

        with open(path, 'w') as f:
            w = csv.writer(f)
            for row in self.rows:
                w.writerow(row)

    def load_rows(self, row_generator):
        from metatab import TermGenerator, TermInterpreter

        term_gen = list(TermGenerator(row_generator))

        term_interp = TermInterpreter(term_gen)

        last_parents = {}

        for t in term_interp:
            if t.record_term == 'root':
                continue

            if t.parent:
                parent = last_parents[t.parent_term_lc]
                nt = parent.new_child(t.record_term, t.value)

            else:
                if t.join_lc == 'documentation.subtitle':
                    raise Exception()
                section_name = t.section.value if t.section.value else 'Root'
                s = self.get_or_new_section(section_name, t.section.args)
                nt = s.new_term(t.record_term, t.value)

            last_parents[t.record_term_lc] = nt

        return self

    def load_csv(self, file_name):
        """Load a Metatab CSV file into the builder to continue editing it. """
        from metatab import CsvPathRowGenerator
        return self.load_rows(CsvPathRowGenerator(file_name))


class Section(object):
    def __init__(self, name, doc, params=None):

        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'doc', doc)
        object.__setattr__(self, 'terms', [])

        object.__setattr__(self, 'param_names',
                           doc.decl_sections.get(name.lower(), {}).get('args', []) if params is None else list(params)
                           )

    def set_param_names(self, params):
        object.__setattr__(self, 'param_names',
                           self.doc.decl_sections.get(self.name.lower(), {}).get('args',
                                                                                 []) if params is None else list(params)
                           )

    def new_term(self, term, value, **kwargs):
        t = TermRecord(term, value, _parent=None, _section=self, **kwargs)

        self.terms.append(t)
        return t

    def delete_term(self, term):
        """Remove a term from the terms. Must be the identical term, the same object"""
        self.terms.remove(term)

    def __setattr__(self, key, item):
        self.new_term(key, item)

    def args(self, term, d):

        tvm = self.doc.decl_terms.get(term, {}).get('termvaluename', '@value')

        lower_d = {k.lower(): v for k, v in d.items()}

        args = []
        for n in [tvm] + self.param_names:
            args.append(lower_d.get(n.lower(), ''))

            try:
                del lower_d[n.lower()]
            except KeyError:
                pass

        return term, args, lower_d

    @property
    def rows(self):
        """Yield rows for the section"""
        for t in self.terms:
            for row in t.rows:
                term, value = row # Value can either be a string, or a dict

                if isinstance(value, dict): # Dict is for properties, which might be arg-children
                    term, args, remain = self.args(term, value)
                    yield term, args

                    # 'remain' is all of the children that didn't have an arg-child column -- the
                    # section didn't have a column heder for that ther.
                    for k, v in remain.items():

                        yield term.split('.')[-1] + '.' + k, v
                else:
                    yield row


class TermRecord(object):
    def __init__(self, _term, _value, _parent=None, _section=None, **kwargs):
        self.term = _term
        self.value = _value
        self.parent = _parent
        self.section = _section
        self.children = []
        self.args = {}

        if self.parent:
            self.qualified_term = self.parent.term.lower() + '.' + self.term.lower()
        else:
            self.qualified_term = 'root.' + self.term.lower()

        for k, v in kwargs.items():
            self.new_child(k, v)

    def new_child(self, term, value, **kwargs):
        c = TermRecord(term, value, _parent=self, _section=self.section, **kwargs)
        self.children.append(c)
        return c

    @property
    def is_terminal(self):
        return len(self.children) == 0

    @property
    def rows(self):
        """Yield rows"""

        # Translate the term value name so it can be assigned to a parameter.
        tvm = self.section.doc.decl_terms.get(self.qualified_term, {}).get('termvaluename', '@value')

        # Terminal children have no arguments, just a value. Here we put the terminal children
        # in a property arry, so they can be written to the parent's arg-children columns
        # if the section has any.
        properties = {tvm: self.value}
        for c in self.children:
            if c.is_terminal:
                properties[c.term] = c.value
        yield (self.qualified_term, properties)

        # The non-terminal children have to get yielded normally -- they can't be arg-children
        for c in self.children:
            if not c.is_terminal:
                for row in c.rows:
                    yield row