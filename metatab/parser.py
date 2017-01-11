# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Parser for the Simple Data Package format. The parser consists of several iterable generator
objects.

"""

ROOT_TERM = 'root'  # No parent term -- no '.' --  in term cell
ELIDED_TERM = '<elided_term>'  # A '.' in term cell, but no term before it.

import copy
import json
from cStringIO import StringIO
from collections import OrderedDict, MutableSequence

import six
import unicodecsv as csv
from exc import IncludeError, ParserError, MetatabError
from generate import generateRows, CsvPathRowGenerator
from os.path import dirname, join, split, exists
from util import declaration_path

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
        # in a property array, so they can be written to the parent's arg-children columns
        # if the section has any.

        properties = {tvm: self.value}

        for c in self.children:
            if c.is_terminal:
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
        if t not in self.terms and t.parent_term_lc == 'root':
            self.terms.append(t)

    def new_term(self, term, value, **kwargs):
        t = Term(term, value, doc=self.doc, parent=None, section=self).new_children(**kwargs)

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
        """Extract the chldren of a term that are arg-children fro mthose that are row-children. """

        # Get the term value name, the property name that should be assigned to the term value.
        tvm = self.doc.decl_terms.get(term, {}).get('termvaluename', '@value')

        # Convert the keys to lower case
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

    def __init__(self, row_gen, remove_special=True):
        """
        :param term_gen: an an iterator that generates terms
        :param remove_special: If true ( default ) remove the special terms from the stream
        :return:
        """

        self._remove_special = remove_special

        self._row_gen = row_gen

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
        try:
            return self._row_gen.path
        except AttributeError:
            return None

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
            'root.synonym': {'termvaluename': 'term', 'childpropertytype': 'sequence'},
            'root.declareterm': {'termvaluename': 'term', 'childpropertytype': 'sequence'},
            'root.declaresection': {'termvaluename': 'section', 'childpropertytype': 'sequence'},
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

    def generate_terms(self, row_gen):
        """An generator that yields term objects, handling includes and argument
        children"""

        try:
            filename = row_gen.path
        except AttributeError:
            filename = '<unknown>'

        for line_n, row in enumerate(row_gen, 1):

            if not row[0].strip() or row[0].strip().startswith('#'):
                continue

            t = Term(row[0].lower(),
                     row[1] if len(row) > 1 else '',
                     row[2:] if len(row) > 2 else [],
                     row=line_n,
                     col=1,
                     file_name=filename)

            if t.term_is('include'):

                if not self.path:
                    raise IncludeError("Can't include because don't know current path", term=t)

                include_ref = t.value.strip('/')

                if include_ref.startswith('http'):
                    path = include_ref
                else:
                    path = join(dirname(filename), include_ref)

                t.value = path

                yield t

                try:
                    for t in self.generate_terms(generateRows(path)):
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
                                   file_name=filename,
                                   parent=t)

    def find_declare_doc(self, d, name):
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

        for fn in (join(d, name), join(d, name+'.csv')):
            if exists(fn):
                return fn

        # substitute well known names
        fn = standard_declares.get(name, name)

        if fn.startswith('http'):
            return fn.strip('/')  # Look for the file on the web
        elif exists(fn):
            return fn
        else:
            raise IncludeError("No local declaration file for '{}' ".format(fn))

    def __iter__(self):

        last_parent_term = 'root'
        last_term_map = {}
        default_term_value_name = '@value'

        last_section = self.root
        last_term_map[ELIDED_TERM] = self.root
        last_term_map[self.root.record_term] = self.root

        try:

            for i, t in enumerate(self.generate_terms(self._row_gen)):

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

                    nt.value = self.find_declare_doc(dirname(nt.file_name), nt.value.strip())

                    if self.path == nt.value:
                        raise IncludeError("Include loop for '{}' ".format(nt.value))

                    try:

                        ti = TermParser(generateRows(nt.value), False)
                        ti.install_declare_terms()
                        list(ti)
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
        """Import a declare doc that has been parsed and converted to a dict. Converts the
        format to make it easier to use. """
        from .exc import DeclarationError
        assert isinstance(d, dict)

        def is_int(value):
            try:
                int(value)
                return True
            except:
                return False

        if 'declaresection' in d:
            for e in d['declaresection']:
                if e:
                    try:
                        self._declared_sections[e['section'].lower()] = {
                            'args': [v for k, v in sorted((k, v) for k, v in e.items() if is_int(k))],
                            'terms': []
                        }
                    except AttributeError:
                        # Hopefully, b/c the DeclareSection entry has no args ( like 'Root' ) and
                        # is getting returned as a Scalar
                        assert isinstance(e, six.string_types)
                        self._declared_sections[e.lower()] = {
                            'args': [],
                            'terms': []
                        }

        if 'declareterm' in d:
            for e in d['declareterm']:

                if not isinstance(e, dict):  # It could be a string in odd cases, ie, no arg children
                    continue

                self._declared_terms[Term.normalize_term(e['term'])] = e

                if e.get('section'):

                    if e['section'].lower() not in self._declared_sections:
                        raise DeclarationError(("Section '{}' is referenced in a term but was not "
                                                "previously declared with DeclareSection").format(e['section']))

                    st = self._declared_sections[e['section'].lower()]['terms']

                    if e['section'] not in st:
                        st.append(e['term'])

        if 'declarevalueset' in d:
            for e in d['declarevalueset']:
                for k, v in self._declared_terms.items():
                    if 'valueset' in v and e.get('name', None) == v['valueset']:
                        v['valueset'] = e['value']

        def inherited_children(t):
            """Generate inherited children based on a terms InhertsFrom property"""
            if not t.get('inheritsfrom'):
                return

            if not 'section' in t :
                raise DeclarationError("DeclareTerm for '{}' must specify a section to use InheritsFrom"
                                       .format(t['term']))

            t_p, t_r = Term.split_term(t['term'])
            ih_p, ih_r = Term.split_term(t['inheritsfrom'])

            # The inherited terms must come from the same section
            section_terms = self._declared_sections[t['section'].lower()]['terms']

            for st_name in section_terms:
                if st_name.lower().startswith(ih_r.lower()+'.'):

                    st_p, st_r = Term.split_term(st_name)
                    # Yield the term, but replace the parent part
                    subtype_name =  t_r+'.'+st_r

                    subtype_d = dict(self._declared_terms[st_name.lower()].items())
                    subtype_d['inheritsfrom'] = '';
                    subtype_d['term'] = subtype_name

                    yield subtype_d

        for key, t in self._declared_terms.items():
            for ih in list(inherited_children(t)):
                self._declared_terms[ih['term'].lower()] = ih


class MetatabDoc(object):
    def __init__(self, terms=None, decl=None):

        self._term_parser = terms

        self.decl_terms = {}
        self.decl_sections = {}

        self.terms = []
        self.sections = OrderedDict()

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

            if t.record_term_lc == 'section':
                self.add_section(t)
            elif t.record_term_lc == 'root':
                t.doc = self
                self.root = t
            elif t.parent_term_lc == 'root':
                self.add_term(t)

        try:
            dd = terms.declare_dict

            self.decl_terms.update(dd['terms'])
            self.decl_sections.update(dd['sections'])

        except AttributeError as e:
            pass

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
                yield ['Section', s.value] + s.param_names

            for row in s.rows:
                term, value = row

                term = term.replace('root.', '').title()

                try:
                    yield [term] + value
                except:
                    yield [term] + [value]

    def as_csv(self):
        """Return a CSV representation as a string"""

        s = StringIO()
        w = csv.writer(s)
        for row in self.rows:
            w.writerow(row)

        return s.getvalue()

    def write_csv(self, path):

        with open(path, 'w') as f:
            f.write(self.as_csv())


def parse_file(file_name):
    return TermParser(CsvPathRowGenerator(file_name))
