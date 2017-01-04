# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Parser for the Simple Data Package format. The parser consists of several iterable generator
objects.

"""

ROOT_TERM = 'root'  # No parent term -- no '.' --  in term cell
ELIDED_TERM = '<elided_term>'  # A '.' in term cell, but no term before it.

from exc import IncludeError, ParserError
from generate import generateRows
import six

# Well known declarations
standard_declares = {
    'metatab': 'http://assets.metatab.org/metatab.csv'
}


class Term(object):
    """Parses a row into the parts of a term

        Public attributes. These are set externally to the constructor.

        file_name Filename or URL of faile that contains term
        row: Row number of term
        col Column number of term
        term_parent Term was generated from arguments of parent
        child_property_type What datatype to use in dict conversion
        valid Did term pass validation tests? Usually based on DeclaredTerm values.

    """

    def __init__(self, term, value, term_args=[],
                 row=None, col=None, file_name=None,
                 parent=None, doc=None, section=None):
        """

        :param term: Simple or compoint term name
        :param value: Term value, from second column of spreadsheet
        :param term_args: Colums 2+ from term row
        :param term_parent: If set, the term is an arg child, and the term_parent is the parent term.

        """

        def strip_if_str(v):
            try:
                return v.strip()
            except AttributeError:
                return v

        self.term = term
        self.parent_term, self.record_term = Term.split_term_lower(self.term)

        self.value = strip_if_str(value) if value else None
        self.args = [strip_if_str(x) for x in term_args]

        self.section = section  # Name of section the term is in.
        self.doc = doc

        self.file_name = file_name
        self.row = row
        self.col = col

        # When converting to a dict, what dict to to use for the self.value value
        self.term_value_name = '@value'  # May be change in term parsing

        # When converting to a dict, what datatype should be used for this term.
        # Can be forced to list, scalar, dict or other types.
        self.child_property_type = 'any'
        self.valid = None

        self.parent = parent  # If set, term was generated from term args

        # There are some restrictions on what terms can be used for omitted parents,
        # otherwise consecutive terms with elided parents will get nested.
        self.can_be_parent = (not self.parent and self.parent_term != ELIDED_TERM)

        self.children = []  # When terms are linked, hold term's children.

        # This is mostly use when building, not when parsing. It should be folded
        # into the joined terms, probably.
        if self.parent:
            self.qualified_term = self.parent.term.lower() + '.' + self.term.lower()
        else:
            self.qualified_term = 'root.' + self.term.lower()

    @classmethod
    def normalize_term(cls, term):
        return "{}.{}".format(*cls.split_term_lower(term))

    @classmethod
    def split_term(cls, term):
        """
        Split a term in to parent and record term components
        :param term: combined term text
        :return: Tuple of parent and record term
        """
        if '.' in term:
            parent_term, record_term = term.split('.')
            parent_term, record_term = parent_term.strip(), record_term.strip()

            if parent_term == '':
                parent_term = ELIDED_TERM

        else:
            parent_term, record_term = ROOT_TERM, term.strip()

        return parent_term, record_term

    @classmethod
    def split_term_lower(cls, term):
        """
        Like split_term, but also lowercases both parent and record term
        :param term: combined term text
        :return: Tuple of parent and record term

        """

        return tuple(e.lower() for e in Term.split_term(term))

    def file_ref(self):
        """Return a string for the file, row and column of the term."""

        from os.path import split

        if self.file_name is not None and self.row is not None:
            parts = split(self.file_name);
            return "{} {}:{} ".format(parts[-1], self.row, self.col)
        elif self.row is not None:
            return " {}:{} ".format(self.row, self.col)
        else:
            return ''

    def add_child(self, child):
        self.children.append(child)

    def new_child(self, term, value, **kwargs):
        c = Term(term, value, parent=self, doc=self.doc, section=self.section).new_children(**kwargs)
        self.children.append(c)
        return c

    def new_children(self, **kwargs):
        for k, v in kwargs.items():
            self.new_child(k, v)

        return self

    def get_child(self, term):
        for c in self.children:
            if c.term.lower() == term.lower():
                return c
        return c


    def get_or_new_child(self, term, value=None, **kwargs):

        c = self.get_child(term)

        if c is None:
            c = Term(term, value, parent=self, doc=self.doc, section=self.section).new_children(**kwargs)
        else:
            if value is not None:
                c.value = value
            for k, v in kwargs.items():
                c.get_or_new_child(k, v)

    def __getitem__(self, item):
        return self.get_child(item)

    def __setitem__(self, item, value):
        return self.get_or_new_child(item, value)

    @property
    def join(self):
        return "{}.{}".format(self.parent_term, self.record_term)

    @property
    def join_lc(self):
        return "{}.{}".format(self.parent_term_lc, self.record_term_lc)

    @property
    def record_term_lc(self):
        return self.record_term.lower()

    @property
    def parent_term_lc(self):
        return self.parent_term.lower()

    def term_is(self, v):

        if self.record_term_lc == v.lower() or self.join_lc == v.lower():
            return True
        else:
            return False

    @property
    def is_terminal(self):
        return len(self.children) == 0

    def as_dict(self):
        return self._convert_to_dict(self)

    @classmethod
    def _convert_to_dict(cls, term):
        """Converts a record heirarchy to nested dicts.

        :param term: Root term at which to start conversion

        """

        if not term:
            return None

        if term.children:

            d = {}

            for c in term.children:

                if c.child_property_type == 'scalar':
                    d[c.record_term_lc] = cls._convert_to_dict(c)

                elif c.child_property_type == 'sequence':
                    try:
                        d[c.record_term_lc].append(cls._convert_to_dict(c))
                    except (KeyError, AttributeError):
                        # The c.term property doesn't exist, so add a list
                        d[c.record_term_lc] = [cls._convert_to_dict(c)]

                else:
                    try:
                        d[c.record_term_lc].append(cls._convert_to_dict(c))
                    except KeyError:
                        # The c.term property doesn't exist, so add a scalar or a map
                        d[c.record_term_lc] = cls._convert_to_dict(c)
                    except AttributeError as e:
                        # d[c.term] exists, but is a scalar, so convert it to a list

                        d[c.record_term_lc] = [d[c.record_term]] + [cls._convert_to_dict(c)]

            if term.value:
                d[term.term_value_name.lower()] = term.value

            return d

        else:
            return term.value

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

    def __repr__(self):
        return "<Term: {}{}.{} {} {} {}>".format(self.file_ref(), self.parent_term,
                                                 self.record_term, self.value, self.args,
                                                 "P" if self.can_be_parent else "C")

    def __str__(self):
        if self.parent_term == ELIDED_TERM:
            return "{}.{}: {}".format(self.file_ref(), self.record_term, self.value)

        else:
            return "{}{}.{}: {}".format(self.file_ref(), self.parent_term, self.record_term, self.value)


class SectionTerm(Term):

    def __init__(self, name, term='Section', doc=None, term_args=None, row=None, col=None, file_name=None, parent=None):

        self.doc = doc

        section_args = term_args if term_args else self.doc.section_args(name) if self.doc else []

        self.terms = [] # Seperate from children. Sections have contained terms, but no children.

        super(SectionTerm, self).__init__(term,name, term_args=section_args,
                                   parent=parent, doc=doc, row=row, col=col, file_name=file_name)

    @classmethod
    def subclass(cls, t):
        """Change a term into a Section Term"""
        t.doc = None
        t.terms = []
        t.__class__ = SectionTerm
        return t

    @property
    def name(self):
        return self.value

    @property
    def param_names(self):
        return self.args

    def add_term(self, t):
        self.terms.append(t)

    def new_term(self, term, value, **kwargs):
        t = BuilderTerm(term, value, parent=None, section=self).new_children(**kwargs)

        self.terms.append(t)
        return t

    def get_term(self, term):
        for t in self.terms:

            if t.term.lower() == term.lower():
                return t

        return None

    def get_or_new_term(self, term, value=None, **kwargs):

        t = self.get_term(term)

        if not t:
            t = BuilderTerm(term, value, parent=None, section=self).new_children(**kwargs)
        else:
            if value is not None:
                t.value = value

            for k, v in kwargs.items():
                t.get_or_new_child(k, v)

    def delete_term(self, term):
        """Remove a term from the terms. Must be the identical term, the same object"""
        self.terms.remove(term)

    def __getitem__(self, item):
        return self.get_term(item)

    def __setitem__(self, item, value):
        return self.get_or_new_term(item, value)

    def __delitem__(self, item):

        for t in self.terms:
            if t.term.lower() == item.lower():
                self.delete_term(item)

        return

    def __iter__(self):
        for t in self.terms:
            yield t

    def _args(self, term, d):

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
                term, value = row  # Value can either be a string, or a dict

                if isinstance(value, dict):  # Dict is for properties, which might be arg-children
                    term, args, remain = self._args(term, value)
                    yield term, args

                    # 'remain' is all of the children that didn't have an arg-child column -- the
                    # section didn't have a column heder for that ther.
                    for k, v in remain.items():
                        yield term.split('.')[-1] + '.' + k, v
                else:
                    yield row

    def as_dict(self):
        self.children = self.terms
        d = super(SectionTerm, self).as_dict()
        self.children = []
        return d


class TermGenerator(object):
    """Generate terms from a row generator. It will produce a term for each row, and child
    terms for any arguments to the row. """

    def __init__(self, row_gen):
        """

        :param row_gen: an interator that generates rows
        :return:
        """

        from os.path import dirname, basename

        self._row_gen = row_gen

        self._path = self._row_gen.path

    @property
    def path(self):
        return self._path

    def __iter__(self):
        """An interator that generates term objects"""
        from os.path import dirname, join

        for line_n, row in enumerate(self._row_gen, 1):

            if not row[0].strip() or row[0].strip().startswith('#'):
                continue

            t = Term(row[0].lower(),
                     row[1] if len(row) > 1 else '',
                     row[2:] if len(row) > 2 else [],
                     row=line_n,
                     col=1,
                     file_name=self._path)

            if t.term_is('include'):

                if not self._path:
                    raise IncludeError("Can't include because don't know current path"
                                       .format(self._root_directory), term=t)

                include_ref = t.value.strip('/')

                if include_ref.startswith('http'):
                    path = include_ref
                else:
                    path = join(dirname(self._path), include_ref)

                t.value = path

                yield t

                try:
                    for t in TermGenerator(generateRows(path)):
                        yield t
                except IncludeError as e:

                    e.term = t
                    raise

                continue  # Already yielded the include term

            yield t

            # Yield any child terms, from the term row arguments
            if not t.term_is('section') and not t.term_is('header'):
                for col, value in enumerate(t.args, 0):
                    if six.text_type(value).strip():
                        yield Term(t.record_term_lc + '.' + six.text_type(col), six.text_type(value), [],
                                   row=line_n,
                                   col=col + 2,  # The 0th argument starts in col 2
                                   file_name=self._path,
                                   parent=t)


class TermInterpreter(object):
    """Takes a stream of terms and sets the parameter map, valid term names, etc """

    def __init__(self, term_gen, doc=None, remove_special=True):
        """
        :param term_gen: an an iterator that generates terms
        :param remove_special: If true ( default ) remove the special terms from the stream
        :return:
        """

        from collections import defaultdict, OrderedDict

        self._remove_special = remove_special

        self._term_gen = term_gen

        self._param_map = []  # Current parameter map, the args of the last Section term

        # _sections and _terms are loaded from Declare documents, in
        # handle_declare and import_declare_doc. The Declare doc information
        # can also be loaded before parsing, so the Declare term can be eliminated.
        self._declared_sections = {}  # Declared sections and their arguments
        self._declared_terms = {}  # Pre-defined terms, plus TermValueName and ChildPropertyType

        self._doc = doc

        self.errors = set()

        self.root = SectionTerm('Root', term='Root', doc=self._doc, row=0, col=0,
                                file_name=self._term_gen.path if hasattr(self._term_gen, 'path') else None,
                                parent=None)

    @property
    def declared_sections(self):
        """Returned the list of declared sections"""
        return self._declared_sections

    @property
    def synonyms(self):

        syns = {}

        for k, v in self._declared_terms.items():
            if 'synonym' in v:
                syns[k.lower()] = v['synonym']

                if not '.' in k:
                    syns[ROOT_TERM + '.' + k.lower()] = v['synonym']

        return syns

    @property
    def terms(self):
        """Returns a list of pre-defined terms, from the declaration doc. To get parsed terms
        use `parsed_terms`"""

        return self._declared_terms

    @property
    def declare_dict(self):

        # Run the parser, if it has not been run yet.
        if not self.root:
            for _ in self: pass

        return {
            'sections': self._declared_sections,
            'terms': self._declared_terms,
        }

    def install_declare_terms(self):
        self._declared_terms.update({
            'root.section': {'termvaluename': 'name'},
            'root.synonym': {'termvaluename': 'term_name', 'childpropertytype': 'sequence'},
            'root.declareterm': {'termvaluename': 'term_name', 'childpropertytype': 'sequence'},
            'root.declaresection': {'termvaluename': 'section_name', 'childpropertytype': 'sequence'},
            'root.declarevalueset': {'termvaluename': 'name', 'childpropertytype': 'sequence'},
            'declarevalueset.value': {'termvaluename': 'value', 'childpropertytype': 'sequence'},
        })


    def substitute_synonym(self, nt):

        if nt.join_lc in self.synonyms:
            nt.parent_term, nt.record_term = Term.split_term_lower(self.synonyms[nt.join_lc]);

    def errors_as_dict(self):

        errors = []
        for e in self.errors:
            errors.append({
                'file': e.term.file_name,
                'row': e.term.row,
                'col': e.term.col,
                'term': e.term.join,
                'error': str(e)
            })

        return errors


    def as_section_dict(self):
        """Iterate, link terms and convert to a dict. LIke as_dict,
         but the top-level of the dict is section names, containing all of the terms
         in that section"""

        # Run the parser, if it has not been run yet.

        d = {}

        if not self.root:
            for _ in self: pass

        for t in self._parsed_terms:
            if t.parent_term == ROOT_TERM:
                section_name = (t.section.value or 'Root').lower()

                if not section_name in d:
                    d[section_name] = []

                d[section_name].append(t.as_dict())

        return d

    def __iter__(self):
        import copy

        last_parent_term = 'root'
        last_term_map = {}
        default_term_value_name = '@value'

        last_section = self.root
        last_term_map[ELIDED_TERM] = self.root
        last_term_map[self.root.record_term] = self.root

        try:

            for i, t in enumerate(self._term_gen):

                if i == 0:
                    yield self.root

                nt = copy.copy(t)

                if nt.parent_term == ELIDED_TERM:
                    nt.parent_term = last_parent_term
                    nt.parent = last_term_map[last_parent_term]

                # Substitute synonyms
                if nt.join_lc in self.synonyms:
                    nt.parent_term, nt.record_term = Term.split_term_lower(self.synonyms[nt.join_lc]);

                # Remap integer record terms to names from the parameter map
                try:

                    nt.record_term = str(self._param_map[int(t.record_term)])
                except ValueError:
                    pass  # the record term wasn't an integer

                except IndexError:
                    pass  # Probably no parameter map.

                if nt.term_is('root.section'):
                    self._param_map = [p.lower() if p else i for i, p in enumerate(nt.args)]

                    # Parentage should not persist across sections
                    last_parent_term = self.root.record_term

                    last_section = SectionTerm.subclass(nt)

                    yield last_section
                    continue

                if nt.term_is('declare'):
                    from os.path import dirname, join

                    t_val = nt.value.strip()

                    # substitute well known names
                    t_val = standard_declares.get(t_val, t_val)

                    if t_val.startswith('http'):
                        fn = t_val.strip('/')
                    else:
                        fn = join(dirname(nt.file_name), t_val)

                    nt.value = fn

                    if hasattr(self._term_gen, 'path') and self._term_gen.path == fn:
                        raise IncludeError("Include loop for '{}' ".format(fn))

                    try:
                        ti = TermInterpreter(TermGenerator(generateRows(fn)), False)
                        ti.install_declare_terms()
                        self.import_declare_doc(ti.root.as_dict())

                    except IncludeError as e:
                        e.term = t
                        self.errors.add(e)
                        raise

                    default_term_value_name = '@value'

                if nt.term_is('header'):
                    self._param_map = [p.lower() if p else i for i, p in enumerate(nt.args)]
                    default_term_value_name = nt.value.lower()
                    continue

                nt.child_property_type = self._declared_terms.get(nt.join, {}).get('childpropertytype', 'any')

                nt.term_value_name = self._declared_terms.get(nt.join, {}).get('termvaluename', default_term_value_name)

                nt.valid = nt.join_lc in self._declared_terms

                nt.section = last_section
                last_section.add_term(nt)

                if nt.can_be_parent:
                    last_parent_term = nt.record_term
                    # Recs created from term args don't go in the maps.
                    # Nor do record term records with elided parent terms
                    last_term_map[ELIDED_TERM] = nt
                    last_term_map[nt.record_term] = nt

                try:
                    if nt.can_be_parent:
                        parent = last_term_map[nt.parent_term]
                    else:
                        parent = last_term_map[last_parent_term]

                    parent.add_child(nt)
                except KeyError as e:
                    import json
                    raise ParserError(("Failed to find parent term in last term map: {} {} \n" +
                                       "Term: \n    {}\nParents:\n    {}\nSynonyms:\n{}")
                                      .format(e.__class__.__name__, e, nt,
                                              last_term_map.keys(),
                                              json.dumps(self.synonyms, indent=4)))



                yield nt

        except IncludeError as e:
            self.errors.add(e)
            raise

    def import_declare_doc(self, d):
        """Import a declare doc that has been parsed and converted to a dict"""

        def is_int(value):
            try:
                int(value)
                return True
            except:
                return False

        if 'declaresection' in d:
            for e in d['declaresection']:
                if e:
                    self._declared_sections[e['section_name'].lower()] = {
                        'args': [v for k, v in sorted((k, v) for k, v in e.items() if is_int(k))],
                        'terms': []
                    }

        if 'declareterm' in d:
            for e in d['declareterm']:

                if not isinstance(e, dict):  # It could be a string in odd cases
                    continue

                self._declared_terms[Term.normalize_term(e['term_name'])] = e

                if 'section' in e and e['section']:

                    if e['section'].lower() not in self._declared_sections:
                        self._declared_sections[e['section'].lower()] = {
                            'args': [],
                            'terms': []
                        }

                    st = self._declared_sections[e['section'].lower()]['terms']

                    if e['section'] not in st:
                        st.append(e['term_name'])

        if 'declarevalueset' in d:
            for e in d['declarevalueset']:
                for k, v in self._declared_terms.items():
                    if 'valueset' in v and e.get('name', None) == v['valueset']:
                        v['valueset'] = e['value']


class MetatabDoc(object):

    def __init__(self,  decl=None, terms=None):
        from collections import OrderedDict

        import collections

        self.decl_terms = {}
        self.decl_sections = {}

        self.terms = []
        self.sections = OrderedDict()

        if decl is None:
            self.decls = []
        elif not isinstance(decl, collections.MutableSequence):
            self.decls = [decl]
        else:
            self.decls = decl

        self.load_declarations(self.decls)

        if terms:
            self.root = None
            self.load_terms(terms)
        else:
            self.root = SectionTerm('Root', term='Root', doc=self._doc, row=0, col=0,
                                    file_name=None, parent=None)


    def load_declarations(self, decls):
        from metatab import TermInterpreter, TermGenerator
        from metatab import RowGenerator

        for dcl in decls:

            term_interp = TermInterpreter(TermGenerator(RowGenerator([['Declare', dcl]], "<none>")))
            term_interp.run()
            dd = term_interp.declare_dict

            self.decl_terms.update(dd['terms'])
            self.decl_sections.update(dd['sections'])

        return self

    def add_term(self, t):

        # Section terms dont show up in the document as terms
        if isinstance(t, SectionTerm):
            self.add_section(t)
        else:
            self.terms.append(t)

        if t.section:
            t.section = self.add_section(t.section)

    def add_section(self, s):

        assert isinstance(s, SectionTerm)

        if s.value.lower() not in self.sections:
            self.sections[s.value.lower()] = s

        return self.sections[s.value.lower()]

    def section_args(self, section_name):
        """Return section arguments for the named section, if it is defined"""
        return self.decl_sections.get(section_name.lower(), {}).get('args', [])

    def new_section(self, name, params=None):
        """Return a new section"""
        self.sections[name] = SectionTerm(self, name, params, parent=self.root)

        return self.sections[name]

    def get_or_new_section(self, name, params=None):
        """Create a new section or return an existing one of the same name"""
        if name not in self.sections:
            self.sections[name] = SectionTerm(self, name, params, parent = self.root)

        return self.sections[name]

    def get_section(self, name):
        return self.sections[name]

    def __getitem__(self, item):
        return self.get_section(item)

    def __delitem__(self, item):

        if item in self.sections:
            for t in self.sections[item]:
                self.terms.remove(t)

        del self.sections[item.lower()]

    def __contains__(self, item):
        for s in self.sections:
            if s.name.lower() == item.lower():
                return True

        return False

    def __iter__(self):
        for s in self.sections.values():
            yield s

    def find(self, term, section=None):
        """Return a list of terms, possibly in a particular section. Use joined term notation"""

        found = []

        for t in self.parsed_terms:
            if t.join_lc == term.lower() and (section is None or section.lower() == t.section.lower()):
                found.append(t)

        return found

    def find_first(self, term, section=None):
        terms = self.find(term, section)

        if len(terms) > 0:
            return terms[0]
        else:
            return None

    def load_terms(self, terms):
        """Create a builder from a sequence of terms, usually a TermInterpreter"""

        from .exc import MetatabError

        if self.root and len(self.root.children) > 0:
            raise MetatabError("Can't run after adding terms to document.")

        try:
            dd = terms.declare_dict

            self.decl_terms.update(dd['terms'])
            self.decl_sections.update(dd['sections'])
        except AttributeError:
            pass

        for t in terms:
            t.doc = self

            if t.record_term_lc == 'root':
                self.root = t
            else:
                self.add_term(t)

        return self

    def load_rows(self, row_generator):
        from metatab import TermGenerator, TermInterpreter

        term_gen = list(TermGenerator(row_generator))

        term_interp = TermInterpreter(term_gen)

        return self.load_terms(term_interp)

    def load_csv(self, file_name):
        """Load a Metatab CSV file into the builder to continue editing it. """
        from metatab import CsvPathRowGenerator
        return self.load_rows(CsvPathRowGenerator(file_name))

    def as_dict(self):
        """Iterate, link terms and convert to a dict"""

        return self.root.as_dict()

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

    def as_csv(self):
        """Return a CSV representation as a string"""
        import unicodecsv as csv
        from cStringIO import StringIO

        s = StringIO()
        w = csv.writer(s)
        for row in self.rows:
            w.writerow(row)

        return s.getvalue()

    def write_csv(self, path):

        with open(path, 'w') as f:
            f.write(self.as_csv())

        def write_excel(self, path):
            from .excel import write_excel

            return write_excel(path, )


def parse_file(file_name):
    from . import CsvPathRowGenerator

    return TermInterpreter(TermGenerator(CsvPathRowGenerator(file_name)))
