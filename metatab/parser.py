# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Parser for the Metatab format. The parser consists of several iterable generator
objects.

"""
from __future__ import print_function
from appurl import Url, parse_app_url, DownloadError
from rowgenerators import Source, get_generator
ROOT_TERM = 'root'  # No parent term -- no '.' --  in term cell

ELIDED_TERM = '<elided_term>'  # A '.' in term cell, but no term before it.

METATAB_ASSETS_URL = 'http://assets.metatab.org/'

from .terms import Term, SectionTerm, RootSectionTerm

from .exc import IncludeError, DeclarationError, ParserError, GenerateError
from os.path import dirname, join, exists
from .util import declaration_path, import_name_or_class

from functools import lru_cache

# Python2 doesn't have FileNotFoundError
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

class TermParser(object):
    """Takes a stream of terms and sets the parameter map, valid term names, etc """

    # Map term names to subclass objects
    term_classes = {
        'root.section': 'metatab.terms.SectionTerm',
        'root.root': 'metatab.terms.RootSectionTerm'
    }

    def __init__(self, ref,  resolver=None, doc=None, remove_special=True):
        """
        :param term_gen: an an iterator that generates terms
        :param remove_special: If true ( default ) remove the special terms from the stream
        :return:
        """

        self.resolver = resolver or doc.resolver

        assert self.resolver is not None

        self._remove_special = remove_special

        if isinstance(ref, (Url, Source)):
            self._ref = ref
        else:
            self._ref = parse_app_url(ref)

        assert isinstance(self._ref, (Url, Source)), (type(ref), ref)

        self._path = '<none>' # Set after running parse, from row generator

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
        return self._path

    @property
    def doc(self):
        return self._doc

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


    @lru_cache()
    def super_terms(self):
        """Return a dictionary mapping term names to their super terms"""

        return  {k.lower(): v['inheritsfrom'].lower()
                         for k, v in self._declared_terms.items() if 'inheritsfrom' in v}

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
        """
        Replace the record_term and parent_term with a synonym
        :param nt:
        :return:
        """

        if nt.join_lc in self.synonyms:
            nt.parent_term, nt.record_term = Term.split_term_lower(self.synonyms[nt.join_lc]);

    @classmethod
    def register_term_class(cls, term_name, class_or_name):
        """
        Register a Term subclass for a qualified term name.

        :param term_name: Fully-qualified term name. Will be converted to lowercase.
        :param clz: A class, or fully-qualified, dotted class name.
        :return:
        """

        cls.term_classes[term_name.lower()] = class_or_name

    def get_term_class(self, term_name):

        tnl = term_name.lower()


        try:
            return import_name_or_class(self.term_classes[tnl])
        except KeyError:
            pass

        try:
            return import_name_or_class(self.term_classes[self.super_terms()[tnl]])
        except KeyError:
            pass

        return Term

    def errors_as_dict(self):
        """Return parse errors as a dict"""
        errors = []

        for e in self.errors:

            errors.append({
                'file': e.term.file_name,
                'row': e.term.row if e.term else '<unknown>',
                'col': e.term.col if e.term else '<unknown>',
                'term': e.term.join if e.term else '<unknown>',
                'error': str(e)
            })

        return errors

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

        path = None
        while True:
            if exists(name):
                path =name
                break

            try:
                # Look for a local document
                path = declaration_path(name)
                break
            except IncludeError:
                pass

            for fn in (join(d, name), join(d, name + '.csv')):
                if exists(fn):
                    path = fn
                    break
            if path:
                break

            if name.startswith('http'):
                path = name.strip('/')  # Look for the file on the web
                break
            elif exists(name):
                path = name
                break
            else:
                path = self.resolver.find_decl_doc(name)
                break

            raise IncludeError("No local declaration file for '{}'".format(name))

        return parse_app_url(path)

    def find_include_doc(self, d, name):
        """Resolve a name or path for an include doc to a an absolute path or url
        :param name:
        """

        include_ref = name.strip('/')

        if include_ref.startswith('http'):
            path = include_ref
        else:
            if not d:
                raise IncludeError("Can't include '{}' because don't know current path "
                                   .format(name))

            path = join(d, include_ref)

        return parse_app_url(path)

    def generate_terms(self, ref, root, file_type=None):
        """An generator that yields term objects, handling includes and argument
        children.
        :param file_type:
        :param doc:
        :param root:
        :param ref:

        """

        last_section = root
        t = None

        if isinstance(ref, Source):
            row_gen = ref
            ref_path = row_gen.__class__.__name__
        else:
            row_gen = get_generator(ref)
            ref_path = ref.path


        try:
            for line_n, row in enumerate(row_gen, 1):

                if not row or not row[0] or not row[0].strip() or row[0].strip().startswith('#'):
                    continue

                tt = Term(row[0], None) # Just to get the qualified name constructed property

                term_class = self.get_term_class(tt.join_lc)

                t = term_class(tt.join_lc,
                         row[1] if len(row) > 1 else '',
                         row[2:] if len(row) > 2 else [],
                         row=line_n,
                         col=1,
                         file_name=ref_path, file_type=file_type, doc=self.doc)

                if t.value and str(t.value).startswith('#'): # Comments are ignored
                    continue

                if t.term_is('include') or t.term_is('declare'):

                    if t.term_is('include'):
                        resolved = self.find_include_doc(dirname(ref_path), t.value.strip())
                    else:
                        resolved = self.find_declare_doc(dirname(ref_path), t.value.strip())

                    if row_gen.ref == resolved:
                        raise IncludeError("Include loop for '{}' ".format(resolved))

                    yield t

                    try:

                        sub_gen = get_generator(resolved.get_resource().get_target())

                        for t in self.generate_terms(sub_gen, root, file_type=t.record_term_lc):
                            yield t

                        if last_section:
                            yield last_section  # Re-assert the last section

                    except IncludeError as e:
                        e.term = t
                        raise

                    except (OSError,  FileNotFoundError, GenerateError, DownloadError) as e:
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
                        if str(value).strip():

                            term_name = t.record_term_lc + '.' + str(col)

                            term_class = self.get_term_class(term_name)

                            yield term_class(term_name, str(value), [],
                                       row=line_n,
                                       col=col + 2,  # The 0th argument starts in col 2
                                       file_name=ref_path,
                                       file_type=file_type,
                                       parent=t) #,
                                       #doc=None,
                                       #section=last_section)
        except IncludeError as e:
            exc = IncludeError(str(e) + "; in '{}' ".format(ref_path))
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
            target = self._ref.get_resource().get_target() # An AppUrl
        except AttributeError as e:
            target = self._ref # Hopefully a generator

        try:

            for i, t in enumerate(self.generate_terms(target, root)):

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
                    last_section.default_term_value_name = default_term_value_name
                    continue

                elif t.term_is('root.section'):
                    self._param_map = munge_param_map(t)
                    # Parentage should not persist across sections
                    last_parent_term = self.root.record_term

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

                        try:
                            last_term_map[t.parent_term].add_child(t)
                        except KeyError:
                            raise ParserError("No parent term for '{}' in term '{}', row = {}"
                                              .format(t.parent_term, t.term, t.row))

                    if t.parent_term_lc == 'root':
                        last_section.add_term(t)

                if t.file_type == 'declare':
                    self.manage_declare_terms(t)
                    # Declare terms aren't part of document, so they aren't yieled
                else:

                    yield t

        except IncludeError as e:
            assert e is not None
            self.errors.add(e)
            raise

    def manage_declare_terms(self, t):

        if t.term_is('root.declaresection'):
            self.add_declared_section(t)

        elif t.term_is('root.declareterm'):
            self.add_declared_term(t)

        elif t.term_is('value.*'):
            self.add_value_set_value(t)

        self.super_terms.cache_clear()

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

        td = {k: v for k, v in t.arg_props.items() if v.strip()}
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
        disp_value = t.arg_props.get('displayvalue')

        for k, v in self._declared_terms.items():
            if 'valuesetname' in v and vs_name == v['valuesetname'].lower():
                if value not in v['values']:
                    v['values'][value] = disp_value

