# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Generate rows from a variety of paths, references or other input
"""
import collections
from collections import OrderedDict, MutableSequence
from itertools import islice
from os.path import isfile, dirname, join

import six
import unicodecsv as csv

from metatab import (TermParser, SectionTerm, Term, generateRows, MetatabError,
                     CsvPathRowGenerator, RootSectionTerm)
from metatab.util import linkify, slugify
from metatab.exc import MetatabError
from rowgenerators import RowGenerator, Url, SelectiveRowGenerator
from rowgenerators.exceptions import SourceError
from rowgenerators.util import reparse_url, parse_url_to_dict, unparse_url_dict
from rowpipe import RowProcessor
from rowgenerators import Url, DownloadError
from os.path import dirname, abspath, isdir, getmtime
from time import time
from .exc import PackageError

import logging

logger = logging.getLogger('doc')

DEFAULT_METATAB_FILE = 'metadata.csv'

BACKUP_METATAB_FILE = 'metadata.xlsx'


def get_cache(clean=False):
    from rowgenerators.util import get_cache, clean_cache

    cache = get_cache('metapack')

    if clean:
        clean_cache(cache)

    return cache


def resolve_package_metadata_url(ref):
    """Re-write a url to a resource to include the likely refernce to the
    internal Metatab metadata"""

    du = Url(ref)

    if du.resource_format == 'zip':
        package_url = reparse_url(ref, fragment=False)
        metadata_url = reparse_url(ref, fragment=DEFAULT_METATAB_FILE)

    elif du.target_format == 'xlsx' or du.target_format == 'xls':
        package_url = reparse_url(ref, fragment=False)
        metadata_url = reparse_url(ref, fragment='meta')

    elif du.resource_file == DEFAULT_METATAB_FILE:
        metadata_url = reparse_url(ref)
        package_url = reparse_url(ref, path=dirname(parse_url_to_dict(ref)['path']), fragment=False) + '/'

    elif du.target_format == 'csv':
        package_url = reparse_url(ref, fragment=False)
        metadata_url = reparse_url(ref)

    elif du.proto == 'file':
        p = parse_url_to_dict(ref)

        if isfile(p['path']):
            metadata_url = reparse_url(ref)
            package_url = reparse_url(ref, path=dirname(p['path']), fragment=False)
        else:

            p['path'] = join(p['path'], DEFAULT_METATAB_FILE)
            package_url = reparse_url(ref, fragment=False, path=p['path'].rstrip('/') + '/')
            metadata_url = unparse_url_dict(p)

        # Make all of the paths absolute. Saves a lot of headaches later.
        package_url = reparse_url(package_url, path=abspath(parse_url_to_dict(package_url)['path']))
        metadata_url = reparse_url(metadata_url, path=abspath(parse_url_to_dict(metadata_url)['path']))

    else:
        metadata_url = join(ref, DEFAULT_METATAB_FILE)
        package_url = reparse_url(ref, fragment=False)

    # raise PackageError("Can't determine package URLs for '{}'".format(ref))

    return package_url, metadata_url


def open_package(ref, cache=None, clean_cache=False):
    from rowgenerators.util import clean_cache as rg_clean_cache
    package_url, metadata_url = resolve_package_metadata_url(ref)

    cache = cache if cache else get_cache()

    return MetatabDoc(metadata_url, package_url=package_url, cache=cache)


EMPTY_SOURCE_HEADER = '_NONE_'  # Marker for a column that is in the destination table but not in the source


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

        d['cache'] = self._doc._cache
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

        from .pands import MetatabDataFrame

        d = self.properties

        df = self._upstream_dataframe(limit)

        if df is not None:
            return df

        rg = self.row_generator

        # Just normal data, so use the iterator in this object.
        headers = next(islice(self, 0, 1))
        data = islice(self, 1, None)

        df = MetatabDataFrame(list(data), columns=headers, metatab_resource=self)

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
        from rowgenerators.generators import MetapackSource

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

        from .html import ckan_resource_markdown
        return ckan_resource_markdown(self)


class Reference(Resource):
    def __init__(self, term, base_url, package=None, env=None, code_path=None):
        super().__init__(term, base_url, package, env, code_path)

    def dataframe(self, limit=None):
        """Return a Pandas Dataframe using read_csv or read_excel"""

        from pandas import read_csv
        from rowgenerators import download_and_cache
        from .pands import MetatabDataFrame, MetatabSeries

        df = self._upstream_dataframe(limit)

        if df is not None:
            self._convert_geometry(df)
            return df

        rg = self.row_generator

        # Download, cache and possibly extract an inner file.
        info = download_and_cache(rg.generator.spec, self._doc._cache, logger=None, working_dir='', callback=None)

        try:
            skip = int(self.get_value('startline', 1)) - 1
        except ValueError as e:
            skip = 0

        df = read_csv(
            info['sys_path'],
            skiprows=skip
        )

        df.columns = self._get_header()

        df.__class__ = MetatabDataFrame
        df.metatab_resource = self
        df.metatab_errors = {}

        for c in df.columns:
            df[c].__class__ = MetatabSeries


        return df


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
            verterm = doc['Root'].new_term('Root.Version',1)

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

    def add_datafile(self, url, name, schema=None, title=None, description=None,
                     startline=None, encoding=None, headers=None):
        pass

    def add_contact(self):
        pass

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
        import sys
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

        Dist = namedtuple('Dist','type url term')

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

        term_interp = TermParser(row_generator)

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
        from .html import html
        return html(self)

    @property
    def markdown(self):
        from .html import markdown
        return markdown(self)
