# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Generate rows from a variety of paths, references or other input
"""
import collections
import logging
from collections import OrderedDict, MutableSequence
from os.path import dirname, getmtime
from time import time

import six
import unicodecsv as csv
from rowgenerators import Url
from rowgenerators.exceptions import SourceError

from metatab import DEFAULT_METATAB_FILE
from metatab.parser import TermParser
from metatab.generate import generateRows, CsvPathRowGenerator
from metatab.exc import MetatabError
from metatab.util import linkify, slugify
from .terms import SectionTerm, RootSectionTerm, Resource, Reference
from .util import get_cache
from .exc import PackageError

logger = logging.getLogger('doc')


class MetatabDoc(object):
    def __init__(self, ref=None, decl=None, package_url=None, cache=None, clean_cache=False):

        self._cache = cache if cache else get_cache()

        self.decl_terms = {}
        self.decl_sections = {}

        self.terms = []
        self.sections = OrderedDict()
        self.errors = []
        self.package_url = package_url

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
            try:
                self.load_terms(self._term_parser)
            except SourceError as e:
                raise MetatabError("Failed to load terms for document '{}': {}".format(self._ref, e))

            u = Url(self._ref)
            if u.scheme == 'file':
                try:
                    self._mtime = getmtime(u.parts.path)
                except (FileNotFoundError, OSError):
                    self._mtime = 0
            else:
                self._mtime = 0

        else:
            self._ref = None
            self._term_parser = None
            self.root = SectionTerm('Root', term='Root', doc=self, row=0, col=0,
                                    file_name=None, parent=None)
            self.add_section(self.root)
            self._mtime = time()

    @property
    def ref(self):
        return self._ref

    @property
    def path(self):
        """Return the path to the file, if the ref is a file"""

        if not isinstance(self.ref, str):
            return None

        u = Url(self.ref)

        if u.proto != 'file':
            return None

        return u.parts.path

    @property
    def cache(self):
        """Return the file cache used by this document"""
        return self._cache

    @property
    def mtime(self):
        return self._mtime

    def as_version(self, ver):
        """Return a copy of the document, with a different version

        :param ver: A Version number for the returned document. May also be an integer prefixed with '+'
        ( '+1' ) to set the version ahead of this document's version. Prefix with a '-' to set a version behind.

        Typical use of the version math feature is to get the name of a document one version behind:

        >>> doc.as_version('-1')

        """

        doc = self.__class__(self.ref)

        name_t = doc.find_first('Root.Name', section='Root')

        if not name_t:
            raise MetatabError("Document must have a Root.Name Term")

        verterm = name_t.find_first('Name.Version')

        if not verterm:
            verterm = doc.find_first('Root.Version')

        if not verterm:
            verterm = doc['Root'].new_term('Root.Version', 1)

        if isinstance(ver, six.string_types) and (ver[0] == '+' or ver[0] == '-'):
            try:
                int(verterm.value)
            except ValueError:
                raise MetatabError(
                    "When specifying version math, version value in {} term must be an integer".format(verterm.term))

            if ver[0] == '+':
                verterm.value = six.text_type(int(verterm.value) + int(ver[1:]))
            else:
                verterm.value = six.text_type(int(verterm.value) - int(ver[1:]))

        else:
            verterm.value = ver

        doc.update_name(force=True)

        return doc

    @property
    def doc_dir(self):

        from os.path import abspath

        u = Url(self.ref)
        return abspath(dirname(u.parts.path))

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

        if True:
            # Not quite sure about this ...
            if not t.child_property_type:
                t.child_property_type = self.decl_terms \
                    .get(t.join, {}) \
                    .get('childpropertytype', 'any')

            if not t.term_value_name or t.term_value_name == t.section.default_term_value_name:
                t.term_value_name = self.decl_terms \
                    .get(t.join, {}) \
                    .get('termvaluename', t.section.default_term_value_name)

        assert t.section or t.join_lc == 'root.root', t

    def remove_term(self, t):
        """Only removes top-level terms. CHild terms can be removed at the parent. """

        try:
            self.terms.remove(t)
        except ValueError:
            pass

        if t.section and t.parent_term_lc == 'root':
            t.section = self.add_section(t.section)
            t.section.remove_term(t, remove_from_doc=False)

        if t.parent:
            try:
                t.parent.remove_child(t)
            except ValueError:
                pass

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

        # Set the default arguments
        s = self.sections[name.lower()]

        if name.lower() in self.decl_sections:
            s.args = self.decl_sections[name.lower()]['args']

        return s

    def get_or_new_section(self, name, params=None):
        """Create a new section or return an existing one of the same name"""
        if name not in self.sections:
            self.sections[name.lower()] = SectionTerm(name, term_args=params, doc=self, parent=self.root)

        return self.sections[name.lower()]

    def get_section(self, name, default=False):
        try:
            return self.sections[name.lower()]
        except KeyError:
            if default is False:
                raise KeyError("No section for '{}'; sections are: '{}' ".format(name.lower(), self.sections.keys()))
            else:
                return default

    def __getitem__(self, item):
        """Dereference a section name"""

        # Handle dereferencing a list of sections
        if isinstance(item, collections.Iterable) and not isinstance(item, six.string_types):
            for e in item:
                try:
                    return self.__getitem__(e)
                except KeyError:
                    pass
        else:
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

    def find(self, term, value=False, section=None, **kwargs):
        """Return a list of terms, possibly in a particular section. Use joined term notation, such as 'Root.Name' The kwargs arg is used to set term properties, all of which match returned terms, so ``name='foobar'`` will match terms that have a ``name`` property of ``foobar``

        :param term: The type of term to find, in fully-qulified notation, or use '*' for wild cards in either the parent or the record parts, such as 'Root.*', '*.Table' or '*.*'
        :param value: Select terms with a given value
        :param section: The name of the section in which to restrict the search
        :param kwargs:  See additional properties on which to match terms.

        """

        import itertools
        if kwargs:  # Look for terms with particular property values

            terms = self.find(term, value, section)

            found_terms = []

            for t in terms:
                if all(t.get_value(k) == v for k, v in kwargs.items()):
                    found_terms.append(t)

            return found_terms

        def in_section(term, section):

            if section is None:
                return True

            if term.section is None:
                return False

            if isinstance(section, (list, tuple)):
                return any(in_section(t, e) for e in section)
            else:
                return section.lower() == term.section.name.lower()

        # Find any of a list of terms
        if isinstance(term, (list, tuple)):
            return list(itertools.chain(*[self.find(e, value=value, section=section) for e in term]))

        else:
            term = term.lower()

            found = []

            if not '.' in term:
                term = 'root.' + term

            if term.startswith('Root.'):
                term_gen = self.terms
            else:
                term_gen = self.all_terms

            for t in term_gen:

                if t.join_lc == 'root.root':
                    continue

                assert t.section or t.join_lc == 'root.root' or t.join_lc == 'root.section', t

                if (t.term_is(term)
                    and in_section(t, section)
                    and (value is False or value == t.value)):
                    found.append(t)

            return found

    def find_first(self, term, value=False, section=None, **kwargs):

        terms = self.find(term, value=value, section=section, **kwargs)

        if len(terms) > 0:
            return terms[0]
        else:
            return None

    def find_first_value(self, term, value=False, section=None, **kwargs):

        term = self.find_first(term, value=value, section=section, **kwargs)

        if term is None:
            return None
        else:
            return term.value

    def get_value(self, term, default=None):
        term = self.find_first(term, value=False)

        if term is None:
            return default
        else:
            return term.value

    def resources(self, name=None, term='Root.Datafile', section='Resources', env=None, clz=Resource,
                  code_path=None):
        """Iterate over every root level term that has a 'url' property, or terms that match a find() value or a name value"""

        base_url = self.package_url if self.package_url else self._ref

        if env is None:
            try:
                env = self.get_lib_module_dict()
            except PackageError:
                pass

        for t in self[section].terms:

            if term and not t.term_is(term):
                continue

            if name and t.get_value('name') != name:
                continue

            if not 'url' in t.properties:
                pass

            resource_term = clz(t, base_url, env=env, code_path=code_path)

            yield resource_term

    def resource(self, name=None, term='Root.Datafile', section='Resources', env=None,
                 clz=Resource, code_path=None):
        """

        :param name:
        :param term:
        :param env: And environment doc ( like a module ) to pass into the row processor
        :return:
        """

        if env is None:
            try:
                env = self.get_lib_module_dict()
            except PackageError:

                pass

        resources = list(self.resources(name=name, term=term, section=section, env=env, clz=clz,
                                        code_path=code_path))

        if not resources:
            return None

        else:
            r = resources[0]
            return r

    def references(self, name=None, term='Root.Reference', section='References', env=None, code_path=None):
        """
        Like resources(), but by default looks for Root.Reference terms in the References section
        :param name: Value of name property for terms to return
        :param term: Fully qualified term name, defaults to Root.Reference
        :param section: Name of section to look in. Defaults to 'References'
        :param env: Environment dict to be passed into resource row generators.
        :return:
        """

        return self.resources(name=name, term=term, section=section, env=env, clz=Reference)

    def reference(self, name=None, term='Root.Reference', section='References', env=None, code_path=None):
        """
        Like resource(), but by default looks for Root.Reference terms in the References section

        :param name: Value of name property for terms to return
        :param term: Fully qualified term name, defaults to Root.Reference
        :param section: Name of section to look in. Defaults to 'References'
        :param env: Environment dict to be passed into resource row generators.
        :return:
        """

        return self.resource(name=name, term=term, section=section, env=env, clz=Reference)

    def distributions(self, type=False):
        """"Return a dict of distributions, or if type is specified, just the first of that type

        """
        from collections import namedtuple

        Dist = namedtuple('Dist', 'type url term')

        def dist_type(url):

            if url.target_file == 'metadata.csv':
                return 'fs'
            elif url.target_format == 'xlsx':
                return 'excel'
            elif url.resource_format == 'zip':
                return "zip"
            elif url.target_format == 'csv':
                return "csv"

            else:

                return "unk"

        dists = []

        for d in self.find('Root.Distribution'):

            u = Url(d.value)

            t = dist_type(u)

            if type == t:
                return Dist(t, u, d)
            elif type is False:
                dists.append(Dist(t, u, d))

        return dists

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

        term_interp = TermParser(self, row_generator)

        return self.load_terms(term_interp)

    def load_csv(self, file_name):
        """Load a Metatab CSV file into the builder to continue editing it. """
        return self.load_rows(CsvPathRowGenerator(file_name))

    def get_lib_module_dict(self):
        """Load the 'lib' directory as a python module, so it can be used to provide functions
        for rowpipe transforms. This only works filesystem packages"""

        from os.path import dirname, abspath, join, isdir
        from importlib import import_module
        import sys

        u = Url(self.ref)
        if u.proto == 'file':

            doc_dir = dirname(abspath(u.parts.path))

            # Add the dir with the metatab file to the system path
            sys.path.append(doc_dir)

            if not isdir(join(doc_dir, 'lib')):
                return {}

            try:
                m = import_module("lib")
                return {k: v for k, v in m.__dict__.items() if not k.startswith('__')}
            except ImportError as e:

                raise PackageError("Failed to import python module form 'lib' directory: ", str(e))

        else:
            return {}

    def cleanse(self):
        """Clean up some terms, like ensuring that the name is a slug"""
        from .util import slugify

        self.ensure_identifier()

        identifier = self.find_first('Root.Identifier', section='Root')

        name = self.find_first('Root.Name', section='Root')

        try:
            self.update_name()
        except MetatabError:

            if name and name.value:
                name.value = slugify(name.value)
            elif name:
                name.value = slugify(identifier.value)
            else:
                self['Root']['Name'] = slugify(identifier.value)

    def ensure_identifier(self):
        from uuid import uuid4

        identifier = self.find_first('Root.Identifier', section='Root')

        if not identifier:
            self['Root'].new_term('Root.Identifier', six.text_type(uuid4()))

            identifier = self.find_first('Root.Identifier', section='Root')
            assert identifier is not None

    def update_name(self, force=False, create_term=False):
        """Generate the Root.Name term from DatasetName, Version, Origin, TIme and Space"""

        updates = []

        self.ensure_identifier()

        orig_name = self.find_first_value('Root.Name')

        if not orig_name:
            if create_term:
                self['Root'].new_term('Root.Name', '')
                orig_name = ''
            else:
                updates.append("No Root.Name, can't update name")
                return updates

        identifier = self.get_value('Root.Identifier')

        datasetname = self.get_value('Root.Dataset')

        if datasetname:

            name = self._generate_identity_name()

            if name != orig_name or force:
                t = self['Root'].get_or_new_term('Root.Name')
                t.value = name
                updates.append("Changed Name")
            else:
                updates.append("Name did not change")

        elif not orig_name:

            if not identifier:
                updates.append("Failed to find DatasetName term or Identity term. Giving up")

            else:
                updates.append("Setting the name to the identifier")
                self['Root'].get_or_new_term('Root.Name', identifier)

        elif orig_name == identifier:
            updates.append("Name did not change")

        else:
            # There is no DatasetName, so we can't gneerate name, and the Root.Name is not empty, so we should
            # not set it to the identity.
            updates.append("No Root.Dataset, so can't update the name")

        return updates

    def _generate_identity_name(self):

        name_t = self.find_first('Root.Name', section='Root')

        name = name_t.value

        datasetname = name_t.get_value('Name.Dataset', self.get_value('Root.Dataset'))

        ver_value = name_t.get_value('Name.Version', self.get_value('Root.Version'))
        # Excel like to make integers into floats
        try:
            if int(ver_value) == float(ver_value):
                version = int(ver_value)

        except (ValueError, TypeError):
            version = ver_value

        # The Name.* version is deprecated, but still exists in some older
        # files. It should be change to a deprecation warning
        origin = name_t.get_value('Name.Origin', self.get_value('Root.Origin'))
        time = name_t.get_value('Name.Time', self.get_value('Root.Time'))
        space = name_t.get_value('Name.Space', self.get_value('Root.Space'))
        grain = name_t.get_value('Name.Grain', self.get_value('Root.Grain'))
        variant = name_t.get_value('Name.Variant', self.get_value('Root.Variant'))

        parts = [slugify(str(e).replace('-', '_')) for e in (
            origin, datasetname, time, space, grain, variant, version)
                 if e and str(e).strip()]

        return '-'.join(parts)

    def as_dict(self, replace_value_names=True):
        """Iterate, link terms and convert to a dict"""

        # This function is a hack, due to confusion between the root of the document, which
        # should contain all terms, and the root section, which has only terms that are not
        # in another section.

        r = RootSectionTerm(doc=self)

        for s in self:  # Iterate over sections
            for t in s:  # Iterate over the terms in each section.
                r.terms.append(t)

        return r.as_dict(replace_value_names)

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

    @property
    def lines(self):
        """Iterate over all of the rows as text lines"""

        for s_name, s in self.sections.items():

            # Yield the section header
            if s.name != 'Root':
                yield ('Section', s.value)

            # Yield all of the rows for terms in the section
            for row in s.rows:
                term, value = row

                if not isinstance(value, (list, tuple)):
                    value = [value]

                term = term.replace('root.', '').title()
                yield (term, value[0])

                children = list(zip(s.property_names, value[1:]))

                record_term = term.split('.')[-1]

                for prop, value in children:
                    if value and value.strip():
                        child_t = record_term + '.' + (prop.title())
                        yield (child_t, value)

    @property
    def all_terms(self):
        """Iterate over all of the terms. The self.terms property has only root level terms. This iterator
        iterates over all terms"""

        for s_name, s in self.sections.items():

            # Yield the section header
            if s.name != 'Root':
                yield s

            # Yield all of the rows for terms in the section
            for rterm in s:
                yield rterm
                for d in rterm.descendents:
                    yield d

    def as_csv(self):
        """Return a CSV representation as a string"""

        from io import BytesIO

        s = BytesIO()
        w = csv.writer(s)
        for row in self.rows:
            w.writerow(row)

        return s.getvalue()

    def write_csv(self, path=None):
        from rowgenerators import Url

        self.cleanse()

        if path is None:
            if isinstance(self.ref, str):
                path = self.ref
            else:
                path = DEFAULT_METATAB_FILE

        u = Url(path)

        if u.scheme != 'file':
            raise MetatabError("Can't write file to URL '{}'".format(path))

        with open(u.parts.path, 'wb') as f:
            f.write(self.as_csv())

        return u.parts.path

    def _repr_html_(self, **kwargs):
        """Produce HTML for Jupyter Notebook"""

        def resource_repr(r, anchor=kwargs.get('anchors', False)):
            return "<p><strong>{name}</strong> - <a target=\"_blank\" href=\"{url}\">{url}</a> {description}</p>" \
                .format(name='<a href="#resource-{name}">{name}</a>'.format(name=r.name) if anchor else r.name,
                        description=r.get_value('description', ''),
                        url=r.resolved_url)

        def documentation():

            out = ''

            try:
                self['Documentation']
            except KeyError:
                return ''

            try:
                for t in self['Documentation']:

                    if t.get_value('url'):

                        out += ("\n<p><strong>{} </strong>{}</p>"
                                .format(linkify(t.get_value('url'), t.get_value('title')),
                                        t.get_value('description')
                                        ))

                    else:  # Mostly for notes
                        out += ("\n<p><strong>{}: </strong>{}</p>"
                                .format(t.record_term.title(), t.value))


            except KeyError:
                raise
                pass

            return out

        def contacts():

            out = ''

            try:
                self['Contacts']
            except KeyError:
                return ''

            try:

                for t in self['Contacts']:
                    name = t.get_value('name', 'Name')
                    email = "mailto:" + t.get_value('email') if t.get_value('email') else None

                    web = t.get_value('url')
                    org = t.get_value('organization', web)

                    out += ("\n<p><strong>{}: </strong>{}</p>"
                            .format(t.record_term.title(),
                                    (linkify(email, name) or '') + " " + (linkify(web, org) or '')
                                    ))

            except KeyError:
                pass

            return out

        return """
<h1>{title}</h1>
<p>{name}</p>
<p>{description}</p>
<p>{ref}</p>
<h2>Documentation</h2>
{doc}
<h2>Contacts</h2>
{contact}
<h2>Resources</h2>
<ol>
{resources}
</ol>
""".format(
            title=self.find_first_value('Root.Title', section='Root'),
            name=self.find_first_value('Root.Name', section='Root'),
            ref=self.ref,
            description=self.find_first_value('Root.Description', section='Root'),
            doc=documentation(),
            contact=contacts(),
            resources='\n'.join(["<li>" + resource_repr(r) + "</li>" for r in self.resources()])
        )

    @property
    def html(self):
        raise NotImplementedError()
        # from .html import html
        # return html(self)

    @property
    def markdown(self):
        raise NotImplementedError()
        # from .html import markdown
        return markdown(self)
