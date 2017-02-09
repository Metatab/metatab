# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Generate rows from a variety of paths, references or other input
"""
import six
import unicodecsv as csv
from collections import OrderedDict, MutableSequence
from metatab import TermParser, SectionTerm, Term, generateRows, MetatabError, CsvPathRowGenerator, RootSectionTerm
from rowgenerators import RowGenerator
from rowgenerators.util import reparse_url, parse_url_to_dict, unparse_url_dict
from os.path import join

def resolve_package_metadata_url(ref):
    """Re-write a url to a resource to include the likely refernce to the
    internal Metatab metadata"""
    from rowgenerators import Url
    from os.path import isfile, dirname

    du = Url(ref)

    if du.resource_format == 'zip':
        package_url = ref
        metadata_url = reparse_url(ref, fragment='metadata.csv')
    elif du.target_format == 'xlsx' or du.target_format == 'xls':
        package_url = ref
        metadata_url = reparse_url(ref, fragment='meta')
    elif du.target_format == 'csv':
        metadata_url = ref
        package_url = reparse_url(ref, path=dirname(parse_url_to_dict(ref)['path']))
    elif du.proto == 'file':
        p = parse_url_to_dict(ref)

        if isfile(p['path']):
            metadata_url = ref
            package_url = reparse_url(ref, path=dirname(p['path']))
        else:
            p['path'] = join(p['path'], 'metadata.csv')
            package_url = ref
            metadata_url = unparse_url_dict(p)

    return package_url, metadata_url

def open_package(ref):

    package_url, metadata_url = resolve_package_metadata_url(ref)

    return MetatabDoc(metadata_url, package_url=package_url)

class Resource(Term):

    _common_properties = 'url name description schema'.split()


    def __init__(self, term, base_url, package=None):

        super().__init__(term.term, term.value, term.args,
                 term.row, term.col,
                 term.file_name, term.file_type,
                 term.parent, term.doc, term.section)

        self.__dict__.update(term.properties)
        self.base_url = base_url
        self.package = package

        self.__initialised = True

        assert self.url, term.properties


    def _resolved_url(self):
        """Return a URL that propery combines the base_url and a possibly relative
        resource url"""

        from os.path import join, dirname
        from rowgenerators import Url

        u = Url(self.base_url)

        nu = u.component_url(self.url)
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
            return object.__setattr__(self, item, value)

        elif item in self.__dict__:
            object.__setattr__(self, item, value)

        else:
            self.__setitem__(item, value)

    def get(self, attr, default=None):

        try:
            return self.__getattr__(attr)
        except AttributeError:
            return default

    @property
    def headers(self):
        """Return the headers for the resource"""

    def __iter__(self):
        """Iterate over the resource's rows"""

        d = self.properties

        d['url'] = self.resolved_url

        rg = RowGenerator(**d)

        if six.PY3:
            yield from rg
        else:
            for row in rg:
                yield row


class MetatabDoc(object):
    def __init__(self, ref=None, decl=None, package_url=None, cache=None):

        self._cache = cache

        self.decl_terms = {}
        self.decl_sections = {}

        self.terms = []
        self.sections = OrderedDict()
        self.errors = []
        self.package_url=package_url

        if decl is None:
            self.decls = []
        elif not isinstance(decl, MutableSequence):
            self.decls = [decl]
        else:
            self.decls = decl

        self.load_declarations(self.decls)

        if ref:
            self._ref = ref
            self.root = None
            self._term_parser = TermParser(self._ref, doc=self)
            self.load_terms(self._term_parser)
        else:
            self._ref = None
            self._term_parser = None
            self.root = SectionTerm('Root', term='Root', doc=self, row=0, col=0,
                                    file_name=None, parent=None)
            self.add_section(self.root)

    def load_declarations(self, decls):

        term_interp = TermParser(generateRows([['Declare', dcl] for dcl in decls], cache=self._cache), doc=self)
        list(term_interp)
        dd = term_interp.declare_dict

        self.decl_terms.update(dd['terms'])
        self.decl_sections.update(dd['sections'])

        return self

    def add_term(self, t, add_section=True):
        t.doc = self

        if t in self.terms:
            return

        assert t.section or t.join_lc == 'root.root', t

        # Section terms don't show up in the document as terms
        if isinstance(t, SectionTerm):
            self.add_section(t)
        else:
            self.terms.append(t)

        if add_section and t.section and t.parent_term_lc == 'root':
            t.section = self.add_section(t.section)
            t.section.add_term(t)

        assert t.section or t.join_lc == 'root.root', t

    def remove_term(self, t):
        """Only removes top-level terms. CHild terms can be removed at the parent. """
        self.terms.remove(t)

        if t.section and t.parent_term_lc == 'root':
            t.section = self.add_section(t.section)
            t.section.remove_term(t)

        if t.parent:
            t.parent.remove_child(t)

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
            self.sections[name.lower()] = SectionTerm(name, term_args=params, doc=self, parent=self.root)

        return self.sections[name.lower()]

    def get_section(self, name):
        try:
            return self.sections[name.lower()]
        except KeyError:
            raise KeyError("No section for '{}'; sections are: '{}' ".format(name.lower(), self.sections.keys()))

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
        """Iterate over sections"""
        for s in self.sections.values():
            yield s

    def find(self, term, value=False, section=None):
        """Return a list of terms, possibly in a particular section. Use joined term notation"""
        import itertools

        if isinstance(term, (list, tuple)):
            return list(itertools.chain(*[self.find(e) for e in term]))

        else:
            found = []

            if not '.' in term:
                term = 'root.' + term

            for t in self.terms:

                if t.join_lc == 'root.root':
                    continue

                assert t.section or t.join_lc == 'root.root', t

                if (t.join_lc == term.lower()
                    and (section is None or section.lower() == t.section.name.lower())
                    and (value is False or value == t.value)):
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


    def resources(self, term=None, name=None):
        """Iterate over every root level term that has a 'url' property, or terms that match a find() value or a name value"""

        for t in ( self.terms if term is None else self.find(term) ):

            if 'url' in t.properties and t.properties.get('url') and (name is None or t.properties.get('name') == name):
                yield Resource(t, self.package_url if self.package_url else self._ref)


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
            else:
                # These terms aren't added to the doc because they are attached to a
                # parent term that is added to the doc.
                assert t.parent is not None

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

    def cleanse(self):
        """Clean up some terms, like ensuring that the name is a slug"""
        from .util import slugify
        from uuid import uuid4

        identity = self.find_first('Root.Identifier', section='root')

        if not identity:
            self['Root'].new_term('Root.Identifier', six.text_type(uuid4()))
            identity = self.find_first('Root.Identifier', section='root')
            assert identity is not None

        name = self.find_first('Root.Name', section='root')

        if name and name.value:
            name.value = slugify(name.value)
        elif name:
            name.value = slugify(identity.value)
        else:
            self['Root']['Name'] = slugify(identity.value)

        version = self.find_first('Root.Version', section='root')

        if version and not version.value:
            version.value = 1
        elif not version:
            self['Root']['Version'] = 1

    def as_dict(self):
        """Iterate, link terms and convert to a dict"""

        # This function is a hack, due to confusion between the root of the document, which
        # should contain all terms, and the root section, which has only terms that are not
        # in another section.

        r = RootSectionTerm(doc=self)

        for s in self:  # Iterate over sections
            for t in s:  # Iterate over the terms in each section.
                r.terms.append(t)

        return r.as_dict()

    @property
    def rows(self):
        """Iterate over all of the rows"""

        for s_name, s in self.sections.items():

            # Yield the section header
            if s.name != 'Root':
                yield ['']  # Unecessary, but makes for nice formatting. Should actually be done just before write
                yield ['Section', s.value] + s.property_names

            # Yield all of the rows for terms in the section
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

        self.cleanse()

        with open(path, 'wb') as f:
            f.write(self.as_csv())