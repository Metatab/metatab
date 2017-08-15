# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Special term subclasses
"""

from itertools import islice
from os.path import split

import six
from rowgenerators import reparse_url, RowGenerator, DownloadError, Url
from rowpipe import RowProcessor

from  metatab import parser as psr


from metatab.exc import GenerateError, PackageError
from metatab.parser import ROOT_TERM, ELIDED_TERM
from metatab.util import linkify

EMPTY_SOURCE_HEADER = '_NONE_'  # Marker for a column that is in the destination table but not in the source


class Term(object):
    """Term object represent a row in a Metatab file, and handle interpeting the
        row into the parts of a term

        Public attributes. These are set externally to the constructor.

        file_name Filename or URL of faile that contains term
        row: Row number of term
        col Column number of term
        term_parent Term was generated from arguments of parent
        child_property_type What datatype to use in dict conversion
        valid Did term pass validation tests? Usually based on DeclaredTerm values.

    """

    def __init__(self, term, value, term_args=False,
                 row=None, col=None, file_name=None, file_type=None,
                 parent=None, doc=None, section=None):
        """

        :param term: Simple or compoint term name
        :param value: Term value, from second column of spreadsheet
        :param term_args: Colums 2+ from term row, which become properties
        :param row: Row number in the file where the term appears. Starts at 0
        :param col: Column number, for arg children ( properties )
        :param file_name: The name or url of the file where the term appears.
        :param file_type: Usually None, but may be 'declare' for terms that appear in declare docs.
        :param parent: If set, the term is an arg child, and the term_parent is the parent term.
        :param doc: a MetatabDoc object, for the document the term is being parsed into.


        """

        def strip_if_str(v):
            try:
                return v.strip()
            except AttributeError:
                return v

        self.parent = parent  # If set, term was generated from term args

        self.term = term  # A lot going on in this setter!

        self.value = strip_if_str(value) if value else None
        self.args = [strip_if_str(x) for x in (term_args or [])]

        self._section = None
        self.section = section
        self.doc = doc

        self.file_name = file_name
        self.file_type = file_type
        self.row = row
        self.col = col

        if self.parent:
            assert self.parent.record_term_lc == self.parent_term_lc, (
            term, self.parent.record_term_lc, self.parent_term_lc)

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
        """Add a term to this term's children. Also sets the child term's parent"""
        assert isinstance(child, Term)
        self.children.append(child)
        child.parent = self
        assert not child.term_is("Datafile.Section")

    def new_child(self, term, value, **kwargs):
        """Create a new term and add it to this term as a child. Creates grandchildren from the kwargs.

        :param term: term name. Just the record term
        :param term: Value to assign to the term
        :param term: Term properties, which create children of the child term.

        """

        c = Term(term, str(value), parent=self, doc=self.doc, section=self.section).new_children(**kwargs)
        assert not c.term_is("*.Section")
        self.children.append(c)
        return c

    def remove_child(self, child):
        """Remove the term from this term's children. """
        assert isinstance(child, Term)
        self.children.remove(child)
        self.doc.remove_term(child)

    def new_children(self, **kwargs):
        """Create new children from kwargs"""
        for k, v in kwargs.items():
            self.new_child(k, v)

        return self

    def set_ownership(self):
        """Recursivelt set the parent, section and doc for a children"""
        assert self.section is not None

        for t in self.children:
            t.parent = self
            t._section = self.section
            t.doc = self.doc
            t.set_ownership()

    def find(self, term, value=False):
        """Return a terms by name. If the name is not qualified, use this term's record name for the parent.
        The method will yield all terms with a matching qualified name. """
        if '.' in term:
            parent, term = term.split('.')
            assert parent.lower() == self.record_term_lc, (parent.lower(), self.record_term_lc)

        for c in self.children:
            if c.record_term_lc == term.lower():
                if value is False or c.value == value:
                    yield c

    def find_first(self, term, value=False):
        """Like find(), but returns only the first matching term"""

        if '.' in term:
            parent, term = term.split('.')
            assert parent.lower() == self.record_term_lc, (term, parent.lower(), self.record_term_lc)

        for c in self.children:
            if c.record_term_lc == term.lower():
                if value is False or c.value == value:
                    return c

        return None

    def find_first_value(self, term):
        """Like find_first(), but returns the matching term's value, or None"""

        try:
            return self.find_first(term).value
        except AttributeError:
            return None

    # Deprecated
    def find_value(self, term):
        return self.find_first_value(term)

    def get_or_new_child(self, term, value=False, **kwargs):
        """Find a term, using find_first, and set it's value and properties, if it exists. If
        it does not, create a new term and children. """

        pt, rt = self.split_term(term)

        term = self.record_term + '.' + rt

        c = self.find_first(rt)

        if c is None:
            c = Term(term, value, parent=self, doc=self.doc, section=self.section).new_children(**kwargs)
            assert not c.term_is("Datafile.Section"), (self, c)
            self.children.append(c)

        else:
            if value is not False:
                c.value = value

            for k, v in kwargs.items():
                c.get_or_new_child(k, v)

        # Check that the term was inserted and can be found.
        assert self.find_first(rt)
        assert self.find_first(rt) == c

        return c

    def __getitem__(self, item):
        """Item getter for child property values. Returns the value of this term with given the term's
        term value name"""

        if item.lower() == self.term_value_name.lower():
            return self

        else:

            c = self.find_first(item)
            if c is None:
                raise KeyError("Failed to find key '{}' in term '{}'".format(item, str(self)))

            return c

    def __contains__(self, item):

        if item.lower() == 'value':
            return True

        return item.lower() in self.properties

    def __getattr__(self, item):
        """Maps values to attributes.
        Only called if there *isn't* an attribute with this name
        """
        try:
            # Normal child
            return self.__getitem__(item).value
        except KeyError:
            raise AttributeError(item)

    def get(self, item, default=None):
        """Get a child"""
        try:
            return self[item]
        except KeyError:

            return default

    def get_value(self, item, default=None):
        """Get the value of a child"""
        try:
            return self[item].value
        except (AttributeError, KeyError) as e:
            return default

    def __setitem__(self, item, value):
        """Set the term's value or one of it's properties. If the item name is a property, and the value
        is None, remove the child. """

        if item.lower() == self.term_value_name.lower() or item.lower() == 'value':
            self.value = value

            return self

        elif value is None:
            child = self.find_first(item)
            if child:
                return self.remove_child(child)

        else:

            c = self.get_or_new_child(item, value)

            # There is a bug where these two values may be different by a trailing space
            assert self[item].value == value, "Item value '{}' is different from set value '{}' ".format(
                self[item].value, value)

            return c

    @property
    def term(self):
        return self._term

    @term.setter
    def term(self, v):
        self._term = v

        self.parent_term, self.record_term = Term.split_term_lower(self._term)

        if self.parent and self.parent_term == ROOT_TERM.lower():
            self.parent_term = self.parent.record_term

    @classmethod
    def normalize_term(cls, term):
        """Return a string of the qualified term, all lower cased. """
        return "{}.{}".format(*cls.split_term_lower(term))

    @property
    def join(self):
        """Join the perant and record terms, but don't change the case"""
        return "{}.{}".format(self.parent_term, self.record_term)

    @property
    def join_lc(self):
        """Like join, but returns the term lowercased. """
        return "{}.{}".format(self.parent_term_lc, self.record_term_lc)

    @property
    def record_term_lc(self):
        """Return the lowercased record term name"""
        return self.record_term.lower()

    @property
    def parent_term_lc(self):
        """Return the lowercase parent term name"""
        return self.parent_term.lower()

    @property
    def qualified_term(self):
        """Return the fully qualified term name. The parent will be 'root' if there is no parent term defined. """

        assert self.parent is not None or self.parent_term_lc == 'root'

        if self.parent:
            return self.parent.record_term_lc + '.' + self.record_term_lc
        else:
            return 'root.' + self.record_term_lc

    def term_is(self, v):
        """Return True if the fully qualified name of the term is the same as the argument. If the
        argument is a list or tuple, return  True if any of the term names match.

        Either the parent or the record term can be '*' ( 'Table.*' or '*.Name' ) to match any value for
        either the parent or record term.

        """

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
            elif v_p == '*' and v_r == '*':
                return True
            else:
                return False

        else:

            return any(self.term_is(e) for e in v)

    def aterm_is(self, v):
        """Return True if the fully qualified name of the term is the same as the argument. If the
        argument is a list or tuple, return  True if any of the term names match.

        Either the parent or the record term can be '*' ( 'Table.*' or '*.Name' ) to match any value for
        either the parent or record term.

        """

        raise Exception("Is this used? SHould probably be deleted")

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
            elif v_p == '*' and v_r == '*':
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

        # print({ c.record_term_lc:c.value for c in self.children})
        d[self.term_value_name.lower()] = self.value

        return d

    def as_dict(self, replace_value_names=True):
        """Convert the term, and it's children, to a minimal data structure form, which may
        be a scalar for a term with a single value or a dict if it has multiple proerties. """

        return self._convert_to_dict(self, replace_value_names)

    @classmethod
    def _convert_to_dict(cls, term, replace_value_names=True):
        """Converts a record heirarchy to nested dicts.

        :param term: Root term at which to start conversion

        """

        if not term:
            return None

        if term.children:

            d = {}

            for c in term.children:

                if c.child_property_type == 'scalar':
                    d[c.record_term_lc] = cls._convert_to_dict(c, replace_value_names)

                elif c.child_property_type == 'sequence':
                    try:
                        d[c.record_term_lc].append(cls._convert_to_dict(c, replace_value_names))
                    except (KeyError, AttributeError):
                        # The c.term property doesn't exist, so add a list
                        d[c.record_term_lc] = [cls._convert_to_dict(c, replace_value_names)]

                else:
                    try:
                        d[c.record_term_lc].append(cls._convert_to_dict(c, replace_value_names))
                    except KeyError:
                        # The c.term property doesn't exist, so add a scalar or a map
                        d[c.record_term_lc] = cls._convert_to_dict(c, replace_value_names)
                    except AttributeError as e:
                        # d[c.term] exists, but is a scalar, so convert it to a list

                        d[c.record_term_lc] = [d[c.record_term]] + [cls._convert_to_dict(c, replace_value_names)]

            if term.value:
                if replace_value_names:
                    d[term.term_value_name.lower()] = term.value
                else:
                    d['@value'] = term.value

            return d

        else:
            return term.value

    @property
    def rows(self):
        """Yield rows for the term, for writing terms to a CSV file. """

        # Translate the term value name so it can be assigned to a parameter.
        tvm = self.section.doc.decl_terms.get(self.qualified_term, {}).get('termvaluename', '@value')
        assert tvm
        # Terminal children have no arguments, just a value. Here we put the terminal children
        # in a property array, so they can be written to the parent's arg-children columns
        # if the section has any.

        properties = {tvm: self.value}

        for c in self.children:
            if c.is_terminal:
                if c.record_term_lc:
                    # This is rare, but can happen if a property child is not given
                    # a property name by the section -- the "Section" term has a blank column.
                    properties[c.record_term_lc] = c.value

        yield (self.qualified_term, properties)

        # The non-terminal children have to get yielded normally -- they can't be arg-children
        for c in self.children:
            if not c.is_terminal:
                for row in c.rows:
                    yield row

    @property
    def descendents(self):
        """Iterate over all descendent terms"""

        for c in self.children:
            yield c

            for d in c.descendents:
                yield d

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

    def _repr_html_(self):
        """HTML Representation method for IPYthon Notebook. """

        return ("<p><strong>{}</strong>: {}</p><ul>{}</ul>".format(
            self.qualified_term, linkify(self.value),
            '\n'.join("<li>{}: {}</li>".format(k, linkify(v)) for k, v in self.properties.items() if k)
        ))


class SectionTerm(Term):
    """A Subclass fo Term specificall for Sections """

    def __init__(self, name, term='Section', doc=None, term_args=None,
                 row=None, col=None, file_name=None, file_type=None, parent=None):

        assert doc is not None

        self.doc = doc

        self.default_term_value_name = '@value'
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
        """Returns either the Section terms, or the Header term arguments. Will prefer the
        Header args, if they exist. """
        if self.header_args:
            return self.header_args
        else:
            return self.args

    def add_term(self, t):
        """Add a term to this section and set it's ownership. Should only be used on root level terms"""
        if t not in self.terms:
            if t.parent_term_lc == 'root':
                self.terms.append(t)

                self.doc.add_term(t, add_section=False)

                t.set_ownership()

            else:
                raise GenerateError("Can only add or move root-level terms. Term '{}' parent is '{}' "
                                    .format(t, t.parent_term_lc))

        assert t.section or t.join_lc == 'root.root', t

    def move_term(self, t):
        """Synonym for add_term. Once did other things. Probably should be deprecated. """
        return self.add_term(t)

    def new_term(self, term, value, **kwargs):
        """Create a neew root-level term in this section"""
        t = Term(term, value, doc=self.doc, parent=None, section=self).new_children(**kwargs)

        self.doc.add_term(t)
        return t

    def get_term(self, term, value=False):
        """Synonym for find_first, restructed to this section"""
        return self.doc.find_first(term, value=value, section=self.name)

    def find_first(self, term, value=False):
        """Synonym for find_first, restructed to this section"""
        return self.doc.find_first(term, value=value, section=self.name)

    def find(self, term, value=False):
        return self.doc.find(term, value=value, section=self.name)

    def find_first_value(self, term, value=False):
        return self.doc.find_first_value(term, value=value, section=self.name)

    def get_or_new_term(self, term, value=False, **kwargs):

        t = self.get_term(term, value=value)

        if not t:
            t = self.new_term(term, value, **kwargs)

        else:
            if value is not None:
                t.value = value

            for k, v in kwargs.items():
                t.get_or_new_child(k, v)

        return t

    def remove_term(self, term, remove_from_doc=True):
        """Remove a term from the terms. Must be the identical term, the same object"""

        try:
            self.terms.remove(term)
        except ValueError:
            pass

        if remove_from_doc:
            self.doc.remove_term(term)

    def clean(self):
        """Remove all of the terms from the section, and also remove them from the document"""
        terms = list(self)

        for t in terms:
            self.doc.remove_term(t)

    def sort_by_term(self, order=None):
        """
        Sort the terms in the section.
        :param order: If specified, a list of qualified, lowercased term names. These names will appear
        first in the section, and the remaining terms will be sorted alphabetically. If not specified, all terms are
        alphabetized.
        :return:
        """

        if order is None:
            self.terms = sorted(self.terms, key=lambda e: e.join_lc)
        else:

            all_terms = list(self.terms)
            sorted_terms = []

            for tn in order:
                for t in list(all_terms):

                    if t.term_is(tn):
                        all_terms.remove(t)
                        sorted_terms.append(t)

            sorted_terms.extend(sorted(all_terms, key=lambda e: e.join_lc))

            self.terms = sorted_terms

    def __getitem__(self, item):
        """Synonym for get_term()"""
        return self.get_term(item)

    def __setitem__(self, item, value):
        """Synonym for get_or_new_term()"""
        return self.get_or_new_term(item, value)

    def __delitem__(self, item):
        """Delete all terms that match the given name"""
        for t in self.terms:
            if t.term.lower() == item.lower():
                self.delete_term(item)

        return

    def __iter__(self):
        """Iterate over all terms in the section"""
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

    def as_dict(self, replace_value_names=True):
        """Return the whole section as a dict"""
        old_children = self.children
        self.children = self.terms

        d = super(SectionTerm, self).as_dict(replace_value_names)

        self.children = old_children

        return d


class RootSectionTerm(SectionTerm):
    def __init__(self, file_name=None, doc=None):
        super(RootSectionTerm, self).__init__('Root', 'Root', doc, [], 0, 0, file_name, None)

    def as_dict(self, replace_value_names=True):
        d = super(RootSectionTerm, self).as_dict(replace_value_names)

        if replace_value_names and '@value' in d:
            del d['@value']

        return d


class Resource(Term):
    # These property names should return null if they aren't actually set.
    _common_properties = 'url name description schema'.split()

    def __init__(self, term, base_url, package=None, env=None, code_path=None):

        super(Resource, self).__init__(term.term, term.value, term.args,
                                       term.row, term.col,
                                       term.file_name, term.file_type,
                                       term.parent, term.doc, term.section)

        self._orig_term = term
        self.base_url = base_url
        self.package = package

        self.code_path = code_path

        self._parent_term = term
        self.term_value_name = term.term_value_name
        self.children = term.children

        self.env = env if env is not None else {}

        self.errors = {}  # Typecasting errors

        self.__initialised = True

    @property
    def _self_url(self):
        try:
            if self.url:
                return self.url
        finally:  # WTF? No idea, probably wrong.
            return self.value

    def _resolved_url(self):
        """Return a URL that properly combines the base_url and a possibly relative
        resource url"""

        from rowgenerators.generators import PROTO_TO_SOURCE_MAP

        if self.base_url:
            u = Url(self.base_url)

        else:
            u = Url(self.doc.package_url)  # Url(self.doc.ref)

        if not self._self_url:
            return None

        nu = u.component_url(self._self_url)

        # For some URLs, we ned to put the proto back on.
        su = Url(self._self_url)

        if not su.reparse:
            return su

        if su.proto in PROTO_TO_SOURCE_MAP().keys():
            nu = reparse_url(nu, scheme_extension=su.proto)

        assert nu
        return nu

    def __contains__(self, item):

        if item.lower() == 'value':
            return True

        return item.lower() in self._common_properties or item.lower() in self.properties

    def __getattr__(self, item):
        """Maps values to attributes.
        Only called if there *isn't* an attribute with this name
        """
        try:
            # Normal child
            return self.__getitem__(item).value
        except KeyError:
            if item.lower() in self._common_properties:
                return None
            elif item == 'resolved_url':
                # Looks like properties don't work properly with this method
                return self._resolved_url()
            else:
                raise AttributeError(item)

    def __setattr__(self, item, value):
        """ """

        if '_Resource__initialised' not in self.__dict__:
            # Not initialized yet; set attributes normally.
            assert item != 'url'
            return object.__setattr__(self, item, value)

        elif item in self.__dict__ and not (item.lower() == self.term_value_name.lower() or item.lower() == 'value'):

            assert item != 'url'
            object.__setattr__(self, item, value)

        elif item.lower() == self.term_value_name.lower() or item.lower() == 'value':
            object.__setattr__(self, 'value', value)
            self._orig_term.value = value

        else:
            # Set a property, which is also a child term.
            self.__setitem__(item, value)

    def get(self, attr, default=None):

        try:
            return self.__getattr__(attr)
        except AttributeError:
            return default

    def new_child(self, term, value, **kwargs):
        raise NotImplementedError("DOn't create children from resources. ")

    def _name_for_col_term(self, c, i):

        altname = c.get_value('altname')
        name = c.value if c.value != EMPTY_SOURCE_HEADER else None
        default = "col{}".format(i)

        for n in [altname, name, default]:
            if n:
                return n

    @property
    def schema_name(self):
        """The value of the Name or Schema property"""
        return self.get_value('schema', self.get_value('name'))

    @property
    def schema_table(self):
        """Deprecated. Use schema_term()"""
        return self.schema_term

    @property
    def schema_term(self):
        """Return the Table term for this resource, which is referenced either by the `table` property or the
        `schema` property"""

        t = self.doc.find_first('Root.Table', value=self.get_value('name'))
        frm = 'name'

        if not t:
            t = self.doc.find_first('Root.Table', value=self.get_value('schema'))
            frm = 'schema'

        if not t:
            frm = None

        return t, frm

    @property
    def headers(self):
        """Return the headers for the resource. Returns the AltName, if specified; if not, then the
        Name, and if that is empty, a name based on the column position. These headers
        are specifically applicable to the output table, and may not apply to the resource source. FOr those headers,
        use source_headers"""

        t, _ = self.schema_term

        if t:
            return [self._name_for_col_term(c, i)
                    for i, c in enumerate(t.children, 1) if c.term_is("Table.Column")]
        else:
            return None

    @property
    def source_headers(self):
        """"Returns the headers for the resource source. Specifically, does not include any header that is
        the EMPTY_SOURCE_HEADER value of _NONE_"""

        t, _ = self.schema_term

        if t:
            return [self._name_for_col_term(c, i)
                    for i, c in enumerate(t.children, 1) if c.term_is("Table.Column")
                    and c.get_value('name') != EMPTY_SOURCE_HEADER
                    ]
        else:
            return None

    def columns(self):

        t, _ = self.schema_term

        if not t:
            return

        for i, c in enumerate(t.children):

            if c.term_is("Table.Column"):

                # This code originally used c.properties,
                # but that fails for the line oriented form, where the
                # sections don't have args, so there are no properties.
                p = {}

                for cc in c.children:
                    p[cc.record_term_lc] = cc.value

                p['name'] = c.value

                p['header'] = self._name_for_col_term(c, i)
                yield p

    def row_processor_table(self):
        """Create a row processor from the schema, to convert the text velus from the
        CSV into real types"""
        from rowpipe.table import Table

        type_map = {
            None: None,
            'string': 'str',
            'text': 'str',
            'number': 'float',
            'integer': 'int'
        }

        def map_type(v):
            return type_map.get(v, v)

        doc = self.doc

        table_term = doc.find_first('Root.Table', value=self.get_value('name'))

        if not table_term:
            table_term = doc.find_first('Root.Table', value=self.get_value('schema'))

        if table_term:

            t = Table(self.get_value('name'))

            col_n = 0

            for c in table_term.children:
                if c.term_is('Table.Column'):
                    t.add_column(self._name_for_col_term(c, col_n),
                                 datatype=map_type(c.get_value('datatype')),
                                 valuetype=map_type(c.get_value('valuetype')),
                                 transform=c.get_value('transform')
                                 )
                    col_n += 1

            return t

        else:
            return None

    @property
    def row_generator(self):
        return self._row_generator()

    def _row_generator(self):

        d = self.properties

        d['url'] = self.resolved_url
        d['target_format'] = d.get('format')
        d['target_segment'] = d.get('segment')
        d['target_file'] = d.get('file')
        d['encoding'] = d.get('encoding', 'utf8')

        generator_args = dict(d.items())
        # For ProgramSource generator, These become values in a JSON encoded dict in the PROPERTIE env var
        generator_args['working_dir'] = self._doc.doc_dir
        generator_args['metatab_doc'] = self._doc.ref
        generator_args['metatab_package'] = str(self._doc.package_url)

        # These become their own env vars.
        generator_args['METATAB_DOC'] = self._doc.ref
        generator_args['METATAB_WORKING_DIR'] = self._doc.doc_dir
        generator_args['METATAB_PACKAGE'] = str(self._doc.package_url)

        d['cache'] = self.doc._cache
        d['working_dir'] = self._doc.doc_dir
        d['generator_args'] = generator_args

        return RowGenerator(**d)

    def _get_header(self):
        """Get the header from the deinfed header rows, for use  on references or resources where the schema
        has not been run"""

        try:
            header_lines = [int(e) for e in str(self.get_value('headerlines', 0)).split(',')]
        except ValueError as e:
            header_lines = [0]

        # We're processing the raw datafile, with no schema.
        header_rows = islice(self._row_generator(), min(header_lines), max(header_lines) + 1)

        from tableintuit import RowIntuiter
        headers = RowIntuiter.coalesce_headers(header_rows)

        return headers

    def __iter__(self):
        """Iterate over the resource's rows"""

        headers = self.headers

        # There are several args for SelectiveRowGenerator, but only
        # start is really important.
        try:
            start = int(self.get_value('startline', 1))
        except ValueError as e:
            start = 1

        if headers:  # There are headers, so use them, and create a RowProcess to set data types
            yield headers

            rg = RowProcessor(islice(self._row_generator(), start, None),
                              self.row_processor_table(),
                              source_headers=self.source_headers,
                              env=self.env,
                              code_path=self.code_path)

        else:
            headers = self._get_header()  # Try to get the headers from defined header lines

            yield headers
            rg = islice(self._row_generator(), start, None)

        if six.PY3:
            # Would like to do this, but Python2 can't handle the syntax
            # yield from rg
            for row in rg:
                yield row
        else:
            for row in rg:
                yield row

        try:
            self.errors = rg.errors if rg.errors else {}
        except AttributeError:
            self.errors = {}

    @property
    def iterdict(self):
        """Iterate over the resource in dict records"""

        headers = None

        for row in self:

            if headers is None:
                headers = row
                continue

            yield dict(zip(headers, row))

    def _upstream_dataframe(self, limit=None):

        from rowgenerators.generators import MetapackSource

        rg = self.row_generator

        # Maybe generator has it's own Dataframe method()
        try:
            return rg.generator.dataframe()
        except AttributeError:
            pass

        # If the source is another package, use that package's dataframe()
        if isinstance(rg.generator, MetapackSource):
            try:
                return rg.generator.resource.dataframe(limit=limit)
            except AttributeError:
                if rg.generator.package is None:
                    raise PackageError("Failed to get reference package for {}".format(rg.generator.spec.resource_url))
                if rg.generator.resource is None:
                    raise PackageError(
                        "Failed to get reference resource for '{}' ".format(rg.generator.spec.target_segment))
                else:
                    raise

        return None

    def _convert_geometry(self, df):

        if 'geometry' in df.columns:

            try:
                import geopandas as gpd
                shapes = [row['geometry'].shape for i, row in df.iterrows()]
                df['geometry'] = gpd.GeoSeries(shapes)
            except ImportError:
                raise
                pass

    def dataframe(self, limit=None):
        """Return a pandas datafrome from the resource"""

        raise NotImplementedError()

        # from .pands import MetatabDataFrame

        d = self.properties

        df = self._upstream_dataframe(limit)

        if df is not None:
            return df

        rg = self.row_generator

        # Just normal data, so use the iterator in this object.
        headers = next(islice(self, 0, 1))
        data = islice(self, 1, None)

        # df = MetatabDataFrame(list(data), columns=headers, metatab_resource=self)

        self.errors = df.metatab_errors = rg.errors if hasattr(rg, 'errors') and rg.errors else {}

        return df

    @property
    def sub_package(self):
        """For references to Metapack resoruces, the original package"""
        from rowgenerators.generators import MetapackSource

        rg = self.row_generator

        if isinstance(rg.generator, MetapackSource):
            return rg.generator.package
        else:
            return None

    @property
    def sub_resource(self):
        """For references to Metapack resoruces, the original package"""
        from rowgenerators.generators import MetapackSource

        rg = self.row_generator

        if isinstance(rg.generator, MetapackSource):
            return rg.generator.resource
        else:
            return None

    def _repr_html_(self):

        try:
            return self.sub_resource._repr_html_()
        except AttributeError:
            pass
        except DownloadError:
            pass

        return ("<h3><a name=\"resource-{name}\"></a>{name}</h3><p><a target=\"_blank\" href=\"{url}\">{url}</a></p>" \
                .format(name=self.name, url=self.resolved_url)) + \
               "<table>\n" + \
               "<tr><th>Header</th><th>Type</th><th>Description</th></tr>" + \
               '\n'.join(
                   "<tr><td>{}</td><td>{}</td><td>{}</td></tr> ".format(c.get('header', ''),
                                                                        c.get('datatype', ''),
                                                                        c.get('description', ''))
                   for c in self.columns()) + \
               '</table>'

    @property
    def markdown(self):

        raise NotImplementedError()

        # from .html import ckan_resource_markdown
        # return ckan_resource_markdown(self)


class Reference(Resource):
    def __init__(self, term, base_url, package=None, env=None, code_path=None):
        super().__init__(term, base_url, package, env, code_path)

    def dataframe(self, limit=None):
        """Return a Pandas Dataframe using read_csv or read_excel"""

        from rowgenerators import download_and_cache

        raise NotImplementedError()

        # from pandas import read_csv
        # from .pands import MetatabDataFrame, MetatabSeries

        df = self._upstream_dataframe(limit)

        if df is not None:
            self._convert_geometry(df)
            return df

        rg = self.row_generator

        # Download, cache and possibly extract an inner file.
        info = download_and_cache(rg.generator.spec, self._doc.cache, logger=None, working_dir='', callback=None)

        try:
            skip = int(self.get_value('startline', 1)) - 1
        except ValueError as e:
            skip = 0

        # df = read_csv(info['sys_path'],skiprows=skip)
        # df.__class__ = MetatabDataFrame



        df.columns = self._get_header()

        df.metatab_resource = self
        df.metatab_errors = {}

        for c in df.columns:
            # df[c].__class__ = MetatabSeries
            pass

        return df
