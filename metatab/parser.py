# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Parser for the Simple Data Package format. The parser consists of several iterable generator
objects.

"""
from __future__ import print_function

ROOT_TERM = 'root'  # No parent term -- no '.' --  in term cell
ELIDED_TERM = '<elided_term>'  # A '.' in term cell, but no term before it.

METATAB_ASSETS_URL = 'http://assets.metatab.org/'

import six

from .exc import IncludeError, DeclarationError, GenerateError
from .generate import generateRows, CsvPathRowGenerator, RowGenerator
from os.path import dirname, join, split, exists
from .util import declaration_path
from rowgenerators import SourceError


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
                 row=None, col=None, file_name=None, file_type=None,
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

        self.parent = parent  # If set, term was generated from term args

        self.term = term  # A lot going on in this setter!

        self.value = strip_if_str(value) if value else None
        self.args = [strip_if_str(x) for x in term_args]

        self._section = None
        self.section = section
        self.doc = doc

        self.file_name = file_name
        self.file_type = file_type
        self.row = row
        self.col = col

        # When converting to a dict, what dict to to use for the self.value value
        self.term_value_name = '@value'  # May be change in term parsing

        # When converting to a dict, what datatype should be used for this term.
        # Can be forced to list, scalar, dict or other types.
        self.child_property_type = 'any'
        self.valid = None

        self.children = []  # When terms are linked, hold term's children.

        assert self.file_name is None or isinstance(self.file_name, six.string_types)

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, v):

        # Don't allow sections to be cleared from terms that have has the section set
        # assert not ( v is None and self._section is not None), self

        self._section = v

        if v:
            self._doc = v.doc

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
        child.parent = self

    def new_child(self, term, value, **kwargs):
        c = Term(term, value, parent=self, doc=self.doc, section=self.section).new_children(**kwargs)
        self.children.append(c)
        return c

    def remove_child(self, child):
        assert isinstance(child, Term)
        self.children.remove(child)

    def new_children(self, **kwargs):
        for k, v in kwargs.items():
            self.new_child(k, v)

        return self

    def set_ownership(self):

        assert self.section is not None

        for t in self.children:
            t.parent = self
            t.section = self.section
            t.doc = self.doc
            t.set_ownership()

    def find_first(self, term):
        for c in self.children:
            if c.record_term_lc == term.lower():
                return c
        return None

    def find_value(self, term):
        try:
            return self.find_first(term).value
        except AttributeError:
            return None

    def get_or_new_child(self, term, value=None, **kwargs):

        c = self.find_first(term)

        if c is None:
            c = Term(term, value, parent=self, doc=self.doc, section=self.section).new_children(**kwargs)
        else:
            if value is not None:
                c.value = value
            for k, v in kwargs.items():
                c.get_or_new_child(k, v)

        return c

    def __getitem__(self, item):

        if item.lower() == self.term_value_name.lower():
            return self
        else:
            c = self.find_first(item)
            if c is None:
                raise KeyError
            return c

    def __setitem__(self, item, value):

        if item.lower() == self.term_value_name.lower() or item.lower() == 'value':
            self.value = value
            return self
        else:
            return self.get_or_new_child(item, value)

    @property
    def term(self):
        return self._term

    @term.setter
    def term(self, v):
        self._term = v

        self.parent_term, self.record_term = Term.split_term_lower(self._term)


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

    @property
    def qualified_term(self):

        assert self.parent is not None or self.parent_term_lc == 'root'

        if self.parent:
            return self.parent.record_term_lc + '.' + self.record_term_lc
        else:
            return 'root.' + self.record_term_lc

    def term_is(self, v):

        if isinstance(v, six.string_types):

            if '.' not in v:
                v = 'root.' + v

            v_p, v_r = self.split_term_lower(v)

            if self.join_lc == v.lower():
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
        """Return true if this term has no children"""
        return len(self.children) == 0

    @property
    def is_arg_child(self):
        """Return true if this term was created as a child of another term, from the parent
        term's arguments"""
        return self.col > 1

    @property
    def has_elided_parent(self):
        """Return true if this term had an elided parent; the term stats with '.' """

        return self.parent_term == ELIDED_TERM

    @property
    def properties(self):
        """Return the value and scalar properties as a dictionary"""
        d = dict(zip([str(e).lower() for e in self.section.property_names], self.args))
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
        return "<Term: {}{}.{} {} {}>".format(self.file_ref(), self.parent_term,
                                                 self.record_term, self.value, self.args)

    def __str__(self):

        sec_name = 'None' if not self.section else self.section.name

        if self.parent_term == ELIDED_TERM:
            return "{}.{}: val={} sec={}".format(
                self.file_ref(), self.record_term, self.value, sec_name)

        else:
            return "{}{}.{}: val={} sec={} ".format(
                self.file_ref(), self.parent_term, self.record_term, self.value, sec_name)


class SectionTerm(Term):
    def __init__(self, name, term='Section', doc=None, term_args=None,
                 row=None, col=None, file_name=None, file_type=None, parent=None):

        assert doc is not None

        self.doc = doc

        section_args = term_args if term_args else self.doc.section_args(name) if self.doc else []

        self.terms = []  # Seperate from children. Sections have contained terms, but no children.

        super(SectionTerm, self).__init__(term, name, term_args=section_args,
                                          parent=parent, doc=doc, row=row, col=col,
                                          file_name=file_name, file_type=file_type)

        self.header_args = []  # Set for each header encoundered

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

        if t not in self.terms:
            if t.parent_term_lc == 'root':
                self.terms.append(t)
                t.section = self

                self.doc.add_term(t, add_section=False)

                t.set_ownership()

            else:
                raise GenerateError("Can only add or move root-level terms. Term '{}' parent is '{}' "
                                    .format(t, t.parent_term_lc))

        assert t.section or t.join_lc == 'root.root', t

    def move_term(self, t):
        return self.add_term(t)

    def new_term(self, term, value, **kwargs):
        t = Term(term, value, doc=self.doc, parent=None, section=self).new_children(**kwargs)

        self.doc.add_term(t)
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
            t = self.new_term(term, value, **kwargs)
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

    def sort_by_term(self, order=None):

        self.terms = sorted(self.terms, key=lambda e: e.join_lc)

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

        old_children = self.children
        self.children = self.terms

        d = super(SectionTerm, self).as_dict()

        self.children = old_children

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

    def __init__(self, ref, doc, remove_special=True):
        """
        :param term_gen: an an iterator that generates terms
        :param remove_special: If true ( default ) remove the special terms from the stream
        :return:
        """

        self._remove_special = remove_special

        self._ref = ref

        self._doc = doc

        self._param_map = []  # Current parameter map, the args of the last Section term

        # _sections and _terms are loaded from Declare documents, in
        # handle_declare and import_declare_doc. The Declare doc information
        # can also be loaded before parsing, so the Declare term can be eliminated.
        self._declared_sections = {}  # Declared sections and their arguments
        self._declared_terms = {}  # Pre-defined terms, plus TermValueName and ChildPropertyType

        self.errors = set()

        self.root = RootSectionTerm(file_name=self.path, doc=self._doc)

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
            if v.get('synonym'):
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
            'declaredsections': {'args': [], 'terms': []},

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

        if name.startswith('http'):
            return name.strip('/')  # Look for the file on the web
        elif exists(name):
            return name
        else:
            import requests
            from requests.exceptions import InvalidSchema
            url = METATAB_ASSETS_URL + name + '.csv'
            try:
                # See if it exists online in the official repo
                r = requests.head(url, allow_redirects=False)
                if r.status_code == requests.codes.ok:
                    return url

            except InvalidSchema:
                pass  # It's probably FTP


        raise IncludeError("No local declaration file for '{}'".format(name))

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
    def generate_terms(cls, ref, root, doc=None, file_type=None):
        """An generator that yields term objects, handling includes and argument
        children.

        """

        #Python2 doesn't have FileNotFoundError
        try:
            FileNotFoundError
        except NameError:
            FileNotFoundError = IOError

        # This method is seperate from __iter__ so it can recurse for Include and Declare

        if isinstance(ref, RowGenerator):
            row_gen = ref
            ref = row_gen.path
        else:
            row_gen = generateRows(ref, cache=doc._cache)

            if not isinstance(ref, six.string_types):
                ref = six.text_type(ref)

        last_section = root

        try:
            for line_n, row in enumerate(row_gen, 1):

                if not row or not row[0] or not row[0].strip() or row[0].strip().startswith('#'):
                    continue

                if row[0].lower().strip() == 'section':
                    t = SectionTerm(row[1] if len(row) > 1 else '',
                                    term_args=row[2:] if len(row) > 2 else [],
                                    row=line_n,
                                    col=1,
                                    file_name=ref, file_type=file_type, doc=doc)
                else:
                    t = Term(row[0].lower(),
                             row[1] if len(row) > 1 else '',
                             row[2:] if len(row) > 2 else [],
                             row=line_n,
                             col=1,
                             file_name=ref, file_type=file_type, doc=doc)

                if t.term_is('include') or t.term_is('declare'):

                    if t.term_is('include'):
                        resolved = cls.find_include_doc(dirname(ref), t.value.strip())
                    else:
                        resolved = cls.find_declare_doc(dirname(ref), t.value.strip())

                    if ref == resolved:
                        raise IncludeError("Include loop for '{}' ".format(resolved))

                    yield t

                    try:
                        for t in cls.generate_terms(resolved, root, doc, file_type=t.record_term_lc):
                            yield t

                        if last_section:
                            yield last_section  # Re-assert the last section

                    except IncludeError as e:
                        e.term = t
                        raise

                    except (FileNotFoundError, SourceError) as e:
                        e = IncludeError("Failed to Include; {}".format(e))
                        e.term = t
                        raise e

                    continue  # Already yielded the include/declare term, and includes can't have children

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
                                       file_type=file_type,
                                       parent=t)
        except IncludeError as e:
            from six import text_type
            exc = IncludeError(text_type(e) + "; in '{}' ".format(ref))
            exc.term = e.term if hasattr(e, 'term') else None
            raise exc

    def __iter__(self):

        last_parent_term = 'root'
        last_term_map = {}
        default_term_value_name = '@value'
        last_section = None

        root = RootSectionTerm(file_name='<root>', doc=self._doc)

        self.root = root
        last_section = self.root
        last_term_map[ELIDED_TERM] = self.root
        last_term_map[self.root.record_term] = self.root

        yield self.root

        try:

            for i, t in enumerate(self.generate_terms(self._ref, root, self._doc)):

                # Substitute synonyms
                if t.join_lc in self.synonyms:
                    t.parent_term, t.record_term = Term.split_term_lower(self.synonyms[t.join_lc]);

                # Remap integer record terms to names from the parameter map
                try:
                    t.record_term = str(self._param_map[int(t.record_term)])
                except ValueError:
                    pass  # the record term wasn't an integer

                except IndexError:
                    pass  # Probably no parameter map.

                t.section = last_section

                def munge_param_map(t):
                    return [p.lower() if p else i for i, p in enumerate(t.args)]

                if t.term_is('root.header'):
                    self._param_map = munge_param_map(t)
                    default_term_value_name = t.value.lower()
                    last_section.header_args = t.args
                    continue

                elif t.term_is('root.section'):
                    self._param_map = munge_param_map(t)
                    # Parentage should not persist across sections
                    last_parent_term = self.root.record_term
                    last_section.header_args = []
                    last_section = t
                    default_term_value_name = '@value'
                    t.section = None

                elif t.term_is('root.root'):
                    last_section = t
                    t.section = None

                else:

                    # Case for normal, value-bearing terms

                    t.child_property_type = self._declared_terms \
                        .get(t.join, {}) \
                        .get('childpropertytype', 'any')

                    t.term_value_name = self._declared_terms \
                        .get(t.join, {}) \
                        .get('termvaluename', default_term_value_name)

                    t.valid = t.join_lc in self._declared_terms  # advisory.

                    # Only terms with the term name in the first column can be parents of
                    # other terms. This rule excludes argument terms and terms with an elided parent

                    if t.has_elided_parent:
                        # Elided parent terms refer to the last term that can be a parent
                        t.parent_term = last_parent_term # After this t.has_elided_parent will be False

                        last_term_map[last_parent_term].add_child(t)

                    elif t.is_arg_child:
                        last_term_map[last_parent_term].add_child(t)

                    else:

                        last_parent_term = t.record_term

                        last_term_map[ELIDED_TERM] = t
                        last_term_map[t.record_term] = t

                        last_term_map[t.parent_term].add_child(t)

                    if t.parent_term_lc == 'root':
                        last_section.add_term(t)

                if t.file_type == 'declare':
                    self.manage_declare_terms(t)
                    # Declare terms aren't part of document, so they aren't yieled
                else:
                    yield t

        except IncludeError as e:
            self.errors.add(e)
            raise


    def manage_declare_terms(self, t):

        if t.term_is('root.declaresection'):
            self.add_declared_section(t)

        elif t.term_is('root.declareterm'):
            self.add_declared_term(t)

        elif t.term_is('value.*'):
            self.add_value_set_value(t)

    def add_declared_section(self, t):

        self._declared_sections[t.value.lower()] = {
            'args': [e.strip() for e in t.args if e.strip()],  # FIXME Very suspicious
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

        td = {k: v for k, v in t.properties.items() if v.strip()}
        td['values'] = {}
        td['term'] = t.value

        self._declared_terms[term_name] = td

        def add_term_to_section(td):

            section_name = td.get('section', '').lower()

            if section_name.lower() not in self._declared_sections:
                raise DeclarationError(("Section '{}' is referenced in a term but was not "
                                        "previously declared with DeclareSection, in '{}'")
                                       .format(section_name, t.file_name))

            st = self._declared_sections[td['section'].lower()]['terms']

            if td['term'] not in st:  # Should be a set, but I frequently print JSON for debugging

                st.append(td['term'])

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


def parse_file(file_name):
    return TermParser(CsvPathRowGenerator(file_name))
