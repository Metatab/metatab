# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Parser for the Simple Data Package format. The parser consists of several iterable generator
objects.

"""
from __future__ import print_function
ROOT_TERM = 'root'  # No parent term -- no '.' --  in term cell
ELIDED_TERM = '<elided_term>'  # A '.' in term cell, but no term before it.

import copy
import json
import six

from collections import OrderedDict, MutableSequence


import unicodecsv as csv
from .exc import IncludeError, ParserError, MetatabError, DeclarationError
from .generate import generateRows, CsvPathRowGenerator, RowGenerator
from os.path import dirname, join, split, exists
from .util import declaration_path

# Well known declarations
standard_declares = {
    'metatab': 'http://assets.metatab.org/metatab-latest.csv'
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
            self.qualified_term = self.parent.record_term_lc + '.' + self.record_term_lc
        else:
            self.qualified_term = 'root.' + self.record_term_lc

        assert self.file_name is None or isinstance(self.file_name, six.string_types)

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

        assert self.file_name is None or isinstance(self.file_name, six.string_types)

        if self.file_name is not None and self.row is not None:
            parts = split(self.file_name);
            return "{} {}:{} ".format(parts[-1], self.row, self.col)
        elif self.row is not None:
            return " {}:{} ".format(self.row, self.col)
        else:
            return ''

    def add_child(self, child):
        assert isinstance(child, Term)
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
            if c.record_term_lc == term.lower():
                return c
        return None

    def get_child_value(self, term):
        try:
            return self.get_child(term).value
        except AttributeError:
            return None

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

        if isinstance(v, six.string_types):

            v_p, v_r = self.split_term_lower(v)

            if self.record_term_lc == v.lower() or self.join_lc == v.lower():
                return True
            elif v_r == '*' and v_p == self.parent_term_lc:
                return True
            elif v_p == '*' and v_r == self.record_term_lc:
                return True
            else:
                return False

        else:

            return any(self.term_is(e) for e in v)

    @property
    def is_terminal(self):
        return len(self.children) == 0

    @property
    def properties(self):
        """Return the value and scalar properties as a dictionary"""
        d =  dict(zip([str(e).lower() for e in self.section.property_names], self.args))
        d[self.term_value_name.lower()] = self.value

        return d

    def as_dict(self):
        """Convert the term, and it's children, to a minimal data structure form, which may
        be a scalar for a term with a single value or a dict if it has multiple proerties. """

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
        assert tvm
        # Terminal children have no arguments, just a value. Here we put the terminal children
        # in a property array, so they can be written to the parent's arg-children columns
        # if the section has any.

        properties = {tvm: self.value}

        for c in self.children:
            if c.is_terminal:
                assert c.record_term_lc
                properties[c.record_term_lc] = c.value

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
    def __init__(self, name, term='Section', doc=None, term_args=None,
                 row=None, col=None, file_name=None, parent=None):

        self.doc = doc

        section_args = term_args if term_args else self.doc.section_args(name) if self.doc else []

        self.terms = []  # Seperate from children. Sections have contained terms, but no children.

        super(SectionTerm, self).__init__(term, name, term_args=section_args,
                                          parent=parent, doc=doc, row=row, col=col, file_name=file_name)

        self.header_args = [] # Set for each header encoundered

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
    def property_names(self):
        if self.header_args:
            return self.header_args
        else:
            return self.args

    def add_term(self, t):
        if t not in self.terms and t.parent_term_lc == 'root':
            self.terms.append(t)

    def new_term(self, term, value, **kwargs):
        t = Term(term, value, doc=self.doc, parent=None, section=self).new_children(**kwargs)

        self.terms.append(t)
        return t

    def get_term(self, term):
        term = six.text_type(term)
        for t in self.terms:

            if t.term.lower() == term.lower():
                return t

        return None

    def get_or_new_term(self, term, value=None, **kwargs):

        t = self.get_term(term)

        if not t:
            t = Term(term, value, doc=self.doc, parent=None, section=self).new_children(**kwargs)
        else:
            if value is not None:
                t.value = value

            for k, v in kwargs.items():
                t.get_or_new_child(k, v)

    def remove_term(self, term):
        """Remove a term from the terms. Must be the identical term, the same object"""
        self.terms.remove(term)

    def clean(self):
        """Remove all of the terms from the section, and also remove them from the document"""
        terms = list(self)

        for t in terms:
            self.doc.remove_term(t)

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
        """Extract the chldren of a term that are arg-children from those that are row-children. """

        # Get the term value name, the property name that should be assigned to the term value.
        tvm = self.doc.decl_terms.get(term, {}).get('termvaluename', '@value')

        # Convert the keys to lower case

        lower_d = {k.lower(): v for k, v in d.items()}

        args = []
        for n in [tvm] + self.property_names:
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
        reset_children = False
        if self.terms and not self.children:
            self.children = self.terms
            reset_children = True

        d = super(SectionTerm, self).as_dict()

        if reset_children:
            self.children = []

        return d


class RootSectionTerm(SectionTerm):
    def __init__(self, file_name=None, doc=None):
        super(RootSectionTerm, self).__init__('Root', 'Root', doc, [], 0, 0, file_name, None)

    def as_dict(self):
        d = super(RootSectionTerm, self).as_dict()

        if '@value' in d:
            del d['@value']

        return d


class TermParser(object):
    """Takes a stream of terms and sets the parameter map, valid term names, etc """

    def __init__(self, ref, remove_special=True):
        """
        :param term_gen: an an iterator that generates terms
        :param remove_special: If true ( default ) remove the special terms from the stream
        :return:
        """

        self._remove_special = remove_special

        self._ref = ref

        self._param_map = []  # Current parameter map, the args of the last Section term

        # _sections and _terms are loaded from Declare documents, in
        # handle_declare and import_declare_doc. The Declare doc information
        # can also be loaded before parsing, so the Declare term can be eliminated.
        self._declared_sections = {}  # Declared sections and their arguments
        self._declared_terms = {}  # Pre-defined terms, plus TermValueName and ChildPropertyType

        self.errors = set()

        self.root = RootSectionTerm(file_name=self.path)

        self.install_declare_terms()

    @property
    def path(self):
        """Return the path from the row generator, if it is avilable"""
        try:
            return self._row_gen.path
        except AttributeError:
            return None

    @property
    def declared_sections(self):
        """Returned the list of declared sections"""
        return self._declared_sections

    @property
    def declared_terms(self):
        """Returns a list of pre-defined terms, from the declaration doc. To get parsed terms
        use `parsed_terms`"""

        return self._declared_terms

    @property
    def synonyms(self):
        """Return a dict of term synonyms"""
        syns = {}

        for k, v in self._declared_terms.items():
            k = k.strip()
            if  v.get('synonym'):
                syns[k.lower()] = v['synonym']

                if not '.' in k:
                    syns[ROOT_TERM + '.' + k.lower()] = v['synonym']

        return syns

    @property
    def declare_dict(self):
        """Return declared sections, terms and synonyms as a dict"""
        # Run the parser, if it has not been run yet.
        if not self.root:
            for _ in self: pass

        return {
            'sections': self._declared_sections,
            'terms': self._declared_terms,
            'synonyms': self.synonyms
        }

    def install_declare_terms(self):
        """Set pre-defined terms that are requred for parsing declaration documents"""

        self._declared_terms.update({
            'root.section': {'termvaluename': 'name'},
            'root.synonym': {'termvaluename': 'term', 'childpropertytype': 'sequence'},
            'root.declareterm': {'termvaluename': 'term', 'childpropertytype': 'sequence'},
            'root.declaresection': {'termvaluename': 'section', 'childpropertytype': 'sequence'},
            'root.declarevalueset': {'termvaluename': 'name', 'childpropertytype': 'sequence'},
            'declarevalueset.value': {'termvaluename': 'value', 'childpropertytype': 'sequence'},
        })

        self._declared_sections.update({
            'root': {'args': [], 'terms': []},
            'declaredterms': {'args': [], 'terms': []},
            'declaredsections':  {'args': [], 'terms': []},

        })

    def substitute_synonym(self, nt):

        if nt.join_lc in self.synonyms:
            nt.parent_term, nt.record_term = Term.split_term_lower(self.synonyms[nt.join_lc]);

    def errors_as_dict(self):
        """Return parse errors as a dict"""
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

    @classmethod
    def find_declare_doc(cls, d, name):
        """Given a name, try to resolve the name to a path or URL to
        a declaration document. It will try:

         * The name as a filesystem path
         * The name as a file name in the directory d
         * The name + '.csv' as a name in the directory d
         * The name as a URL
         * The name as a key in the standard_declares dict
         * The name as a path in this module's metatab.declarations package

         """

        if exists(name):
            return name

        try:
            # Look for a local document
            return declaration_path(name)
        except IncludeError:
            pass

        for fn in (join(d, name), join(d, name + '.csv')):
            if exists(fn):
                return fn

        # substitute well known names
        fn = standard_declares.get(name, name)

        if fn.startswith('http'):
            return fn.strip('/')  # Look for the file on the web
        elif exists(fn):
            return fn
        else:
            raise IncludeError("No local declaration file for '{}'".format(fn))

    @classmethod
    def find_include_doc(cls, d, name):
        """Resolve a name or path for an include doc to a an absolute path or url"""

        include_ref = name.strip('/')

        if include_ref.startswith('http'):
            path = include_ref
        else:

            if not d:
                raise IncludeError("Can't include '{}' because don't know current path "
                                   .format(name))

            path = join(d, include_ref)

        return path

    @classmethod
    def generate_terms(cls, ref, root=None):
        """An generator that yields term objects, handling includes and argument
        children"""

        if isinstance(ref, RowGenerator):
            row_gen = ref
            ref = row_gen.path
        else:
            row_gen = generateRows(ref)

            if not isinstance(ref, six.string_types):
                ref = six.text_type(ref)

        root = RootSectionTerm(file_name=ref)

        last_section = root

        yield root

        try:
            for line_n, row in enumerate(row_gen, 1):

                if not row or not row[0] or  not row[0].strip() or row[0].strip().startswith('#'):
                    continue

                if row[0].lower().strip() == 'section':
                    t = SectionTerm(row[1] if len(row) > 1 else '',
                                    term_args=row[2:] if len(row) > 2 else [],
                                    row=line_n,
                                    col=1,
                                    file_name=ref)
                else:
                    t = Term(row[0].lower(),
                             row[1] if len(row) > 1 else '',
                             row[2:] if len(row) > 2 else [],
                             row=line_n,
                             col=1,
                             file_name=ref)

                if t.term_is('include') or t.term_is('declare'):

                    if t.term_is('include'):
                        resolved= cls.find_include_doc(dirname(ref), t.value.strip())
                    else:
                        resolved = cls.find_declare_doc(dirname(ref), t.value.strip())

                    if ref == resolved:
                        raise IncludeError("Include loop for '{}' ".format(resolved))

                    yield t

                    try:
                        for t in cls.generate_terms(resolved, root=root):
                            yield t

                        if last_section:
                            yield last_section # Re-assert the last section

                    except IncludeError as e:
                        e.term = t
                        raise

                    continue  # Already yielded the include term, and includes can't have children

                elif t.term_is('section'):
                    last_section = t

                yield t

                # Yield any child terms, from the term row arguments
                if not t.term_is('section') and not t.term_is('header'):
                    for col, value in enumerate(t.args, 0):
                        if six.text_type(value).strip():
                            yield Term(t.record_term_lc + '.' + six.text_type(col), six.text_type(value), [],
                                       row=line_n,
                                       col=col + 2,  # The 0th argument starts in col 2
                                       file_name=ref,
                                       parent=t)
        except IncludeError as e:
            exc = IncludeError(e.message+"; in '{}' ".format(ref))
            exc.term = e.term if hasattr(e,'term') else None
            raise exc

    def __iter__(self):

        last_parent_term = 'root'
        last_term_map = {}
        default_term_value_name = '@value'
        last_section = None

        try:

            for i, t in enumerate(self.generate_terms(self._ref)):

                yield_term = True

                if t.term_is('root.root') and last_section is None:
                    self.root = t
                    last_section = self.root
                    last_term_map[ELIDED_TERM] = self.root
                    last_term_map[self.root.record_term] = self.root

                # Substitute synonyms
                if t.join_lc in self.synonyms:
                    t.parent_term, t.record_term = Term.split_term_lower(self.synonyms[t.join_lc]);

                if t.parent_term == ELIDED_TERM:
                    t.parent_term = last_parent_term
                    t.parent = last_term_map[last_parent_term]

                # Remap integer record terms to names from the parameter map
                try:
                    t.record_term = str(self._param_map[int(t.record_term)])
                except ValueError:
                    pass  # the record term wasn't an integer

                except IndexError:
                    pass  # Probably no parameter map.

                if t.term_is('root.section') or t.term_is('root.header'):

                    self._param_map = [p.lower() if p else i for i, p in enumerate(t.args)]

                    if t.term_is('root.header'):
                        default_term_value_name = t.value.lower()
                        last_section.header_args = t.args
                    else:
                        # Parentage should not persist across sections
                        last_parent_term = self.root.record_term
                        last_section.header_args = []
                        last_section = t

                        default_term_value_name = '@value'
                    continue

                elif t.term_is('root.root'):
                    last_section = t
                    yield t
                    continue

                t.section = last_section

                continue_flag, yield_term = self.manage_declare_terms(t)

                if continue_flag:
                    continue

                t.child_property_type = self._declared_terms\
                    .get(t.join, {})\
                    .get('childpropertytype', 'any')

                t.term_value_name = self._declared_terms\
                    .get(t.join, {})\
                    .get('termvaluename', default_term_value_name)

                t.valid = t.join_lc in self._declared_terms

                last_section.add_term(t)

                if t.can_be_parent:
                    last_parent_term = t.record_term
                    # Recs created from term args don't go in the maps.
                    # Nor do record term records with elided parent terms
                    last_term_map[ELIDED_TERM] = t
                    last_term_map[t.record_term] = t

                try:

                    if t.can_be_parent:
                        parent = last_term_map[t.parent_term]
                    else:
                        parent = last_term_map[last_parent_term]

                    if yield_term:
                        parent.add_child(t)
                except KeyError as e:

                    raise ParserError(("Failed to find parent term in last term map: {} {} \n" +
                                       "Term: \n    {}\nParents:\n    {}\nSynonyms:\n{}")
                                      .format(e.__class__.__name__, e, t,
                                              last_term_map.keys(),
                                              json.dumps(sorted(self.synonyms.items()), indent=4)))

                if yield_term:
                    yield t

        except IncludeError as e:
            self.errors.add(e)
            raise

    def manage_declare_terms(self, t):

        if t.term_is([
            'declaresection.*',
            'declareterm.*',
            'declarevalueset.*',
            'root.declarevalueset',
            'valueset.section',
            'childpropertytype.section'
        ]):
            return (True, False)

        if t.term_is('root.declaresection'):
            self.add_declared_section(t)
            yield_term = False
        elif t.term_is('root.declareterm'):
            self.add_declared_term(t)
            yield_term = False
        elif t.term_is('value.*'):
            self.add_value_set_value(t)
            yield_term = False
        else:
            yield_term = True

        return (False, yield_term)

    def add_declared_section(self,t):
        from .exc import DeclarationError

        self._declared_sections[t.value.lower()] = {
            'args': [ e.strip() for e in t.args if e.strip()], # FIXME Very suspicious
            'terms': []
        }

    def inherited_children(self, t):
        """Generate inherited children based on a terms InhertsFrom property.
        The input term must have both an InheritsFrom property and a defined Section

        :param t: A subclassed terms -- has an InheritsFrom value
        """

        if not t.get('inheritsfrom'):
            return

        if not 'section' in t:
            raise DeclarationError("DeclareTerm for '{}' must specify a section to use InheritsFrom"
                                   .format(t['term']))

        t_p, t_r = Term.split_term(t['term'])
        ih_p, ih_r = Term.split_term(t['inheritsfrom'])

        # The inherited terms must come from the same section
        section_terms = self._declared_sections[t['section'].lower()]['terms']


        # For each of the terms in the section, look for terms that are children
        # of the term that the input term inherits from. Then yield each of those terms
        # after chang the term name to be a child of the input term.
        for st_name in section_terms:
            if st_name.lower().startswith(ih_r.lower() + '.'):
                st_p, st_r = Term.split_term(st_name)
                # Yield the term, but replace the parent part
                subtype_name = t_r + '.' + st_r

                subtype_d = dict(self._declared_terms[st_name.lower()].items())
                subtype_d['inheritsfrom'] = '';
                subtype_d['term'] = subtype_name

                yield subtype_d

    def add_declared_term(self, t):
        from .exc import DeclarationError

        term_name = Term.normalize_term(t.value)

        td = { k:v  for k, v in t.properties.items() if v.strip()}
        td['values'] = {}
        td['term'] = t.value

        self._declared_terms[term_name] = td

        def add_term_to_section(td):
            section_name = td.get('section', '').lower()

            if section_name.lower() not in self._declared_sections:
                print(self._declared_sections.keys())
                raise DeclarationError(("Section '{}' is referenced in a term but was not "
                                        "previously declared with DeclareSection, in '{}'")
                                       .format(section_name, t.file_name))

            st = self._declared_sections[td['section'].lower()]['terms']

            if td['term'] not in st:  # Should be a set, but I frequently print JSON for debugging
                st.append(term_name)

        if td.get('section'):
            add_term_to_section(td)

        for t in self.inherited_children(td):
            self._declared_terms[Term.normalize_term(t['term'])] = t
            add_term_to_section(t)

    def add_value_set_value(self, t):

        vs_name = t.parent.join_lc
        value = t.value
        disp_value = t.properties.get('displayvalue')

        for k, v in self._declared_terms.items():
            if 'valuesetname' in v and vs_name == v['valuesetname'].lower():
                if value not in v['values']:
                    v['values'][value] = disp_value



class MetatabDoc(object):
    def __init__(self, terms=None, decl=None):

        self._term_parser = terms

        self.decl_terms = {}
        self.decl_sections = {}

        self.terms = []
        self.sections = OrderedDict()
        self.errors = []

        if decl is None:
            self.decls = []
        elif not isinstance(decl, MutableSequence):
            self.decls = [decl]
        else:
            self.decls = decl

        self.load_declarations(self.decls)

        if terms:
            self.root = None
            self.load_terms(terms)
        else:
            self.root = SectionTerm('Root', term='Root', doc=self, row=0, col=0,
                                    file_name=None, parent=None)
            self.add_section(self.root)

    def load_declarations(self, decls):

        for dcl in decls:
            term_interp = TermParser(generateRows([['Declare', dcl]], "<none>"))
            term_interp.run()
            dd = term_interp.declare_dict

            self.decl_terms.update(dd['terms'])
            self.decl_sections.update(dd['sections'])

        return self

    def add_term(self, t):
        t.doc = self

        # Section terms don't show up in the document as terms
        if isinstance(t, SectionTerm):
            self.add_section(t)
        else:
            self.terms.append(t)

        if t.section and t.parent_term_lc == 'root':
            t.section = self.add_section(t.section)
            t.section.add_term(t)

    def remove_term(self, t):
        self.terms.remove(t)

        if t.section and t.parent_term_lc == 'root':
            t.section = self.add_section(t.section)
            t.section.remove_term(t)

    def add_section(self, s):

        s.doc = self

        assert isinstance(s, SectionTerm), str(s)

        # Coalesce sections, and if a foreign term is added with a foreign section
        # it will get re-assigned to the local section
        if s.value.lower() not in self.sections:
            self.sections[s.value.lower()] = s

        return self.sections[s.value.lower()]

    def section_args(self, section_name):
        """Return section arguments for the named section, if it is defined"""
        return self.decl_sections.get(section_name.lower(), {}).get('args', [])

    def new_section(self, name, params=None):
        """Return a new section"""
        self.sections[name.lower()] = SectionTerm(name, term_args=params, doc=self, parent=self.root)

        return self.sections[name.lower()]

    def get_or_new_section(self, name, params=None):
        """Create a new section or return an existing one of the same name"""
        if name not in self.sections:
            self.sections[name] = SectionTerm(name, term_args=params, doc=self, parent=self.root)

        return self.sections[name]

    def get_section(self, name):
        return self.sections[name.lower()]

    def __getitem__(self, item):
        return self.get_section(item)

    def __delitem__(self, item):

        try:
            if item in self.sections:
                for t in self.sections[item]:
                    self.terms.remove(t)

            del self.sections[item.lower()]
        except KeyError:
            # Ignore errors
            pass

    def __contains__(self, item):

        return item.lower() in self.sections

    def __iter__(self):
        for s in self.sections.values():
            yield s

    def find(self, term, value=False, section=None):
        """Return a list of terms, possibly in a particular section. Use joined term notation"""

        found = []

        for t in self.terms:

            if (t.join_lc == term.lower()
                and (section is None or section.lower() == t.section.lower())
                and (value == False or value == t.value)):
                found.append(t)

        return found

    def find_first(self, term, value=False, section=None):
        terms = self.find(term, value=value, section=section)

        if len(terms) > 0:
            return terms[0]
        else:
            return None

    def find_first_value(self, term, value=False, section=None):
        term = self.find_first(term, value=value, section=section)

        if term is None:
            return None
        else:
            return term.value

    def load_terms(self, terms):
        """Create a builder from a sequence of terms, usually a TermInterpreter"""

        if self.root and len(self.root.children) > 0:
            raise MetatabError("Can't run after adding terms to document.")

        for t in terms:

            t.doc = self
            if t.term_is('root.root'):
                self.root = t
                self.add_section(t)
            elif t.term_is('root.section'):
                self.add_section(t)
            elif t.parent_term_lc == 'root':
                self.add_term(t)

        try:
            dd = terms.declare_dict

            self.decl_terms.update(dd['terms'])
            self.decl_sections.update(dd['sections'])

        except AttributeError as e:
            pass

        try:
            self.errors = terms.errors_as_dict()
        except AttributeError:
            self.errors = {}

        return self

    def load_rows(self, row_generator):

        term_interp = TermParser(row_generator)

        return self.load_terms(term_interp)

    def load_csv(self, file_name):
        """Load a Metatab CSV file into the builder to continue editing it. """
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
                yield ['Section', s.value] + s.property_names

            for row in s.rows:
                term, value = row

                term = term.replace('root.', '').title()

                try:
                    yield [term] + value
                except:
                    yield [term] + [value]

    def as_csv(self):
        """Return a CSV representation as a string"""

        from io import BytesIO

        s = BytesIO()
        w = csv.writer(s)
        for row in self.rows:
            w.writerow(row)

        return s.getvalue()

    def write_csv(self, path):

        with open(path, 'wb') as f:
            f.write(self.as_csv())


def parse_file(file_name):
    return TermParser(CsvPathRowGenerator(file_name))
