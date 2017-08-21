# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

""" """

from collections import namedtuple
from genericpath import exists, isfile
from hashlib import sha1
from itertools import islice
from os import walk
from os.path import dirname, abspath, basename, splitext, join, isdir

from six import string_types, text_type
from tableintuit import RowIntuiter

from metapack import MetapackDoc
from metatab import TermParser, Resource, slugify, DEFAULT_METATAB_FILE
from metapack.exc import PackageError
from rowgenerators import Url, get_cache, SourceSpec, RowGenerator, TextEncodingError, enumerate_contents, \
    download_and_cache, DownloadError, get_dflo, reparse_url, parse_url_to_dict, unparse_url_dict
from util import Bunch


class Package(object):
    def __new__(cls, ref=None, cache=None, callback=None, env=None, save_url=None, acl=None):

        from metapack.package.csv import CsvPackage
        from metapack.package.excel import ExcelPackage
        from metapack.package.s3 import S3Package
        from metapack.package.zip import ZipPackage
        from metapack.exc import PackageError

        if cls == Package:

            if isinstance(ref, Url):
                b = Bunch(ref.dict)
            else:
                b = Bunch(Url(ref).dict)

            if b.resource_format in ('xls', 'xlsx'):
                return super(Package, cls).__new__(ExcelPackage)
            elif b.resource_format == 'zip':
                return super(Package, cls).__new__(ZipPackage)
            #elif b.proto == 'gs':
            #    return super(Package, cls).__new__(GooglePackage)
            elif b.proto == 's3':
                return super(Package, cls).__new__(S3Package)
            elif b.resource_format == 'csv' or b.target_format == 'csv':
                return super(Package, cls).__new__(CsvPackage)
            else:
                raise PackageError("Can't determine package type for ref '{}' ".format(ref))

        else:
            return super(Package, cls).__new__(cls)

    def __init__(self, ref=None, cache=None, callback=None, env=None):

        self._cache = cache if cache else get_cache('metapack')
        self._ref = ref
        self._doc = None
        self._callback = callback
        self._env = env if env is not None else {}
        self.source_dir = dirname(Url(ref).path())
        self.init_doc()

    def load_doc(self, ref):

        if isinstance(ref, string_types):
            self._doc = MetapackDoc(ref, cache=self._cache)
        else:
            self._doc = ref

        return self

    def init_doc(self):

        if self._ref:
            self.load_doc(self._ref)
        else:
            self._doc = MetatabDoc()

            if not self._doc.find("Root.Declare"):
                # FIXME. SHould really have a way to insert this term as the first term.
                self.sections.root.new_term('Declare', 'metatab-latest')
                self._doc.load_declarations(['metatab-latest'])

        return self.doc

    def _open(self):
        """Open the package, possibly downloading it to the cache."""
        if not self._cache:
            raise IOError(
                "Package must have a cache, set either in the package constructor, or with the METAPACK_CACHE env var")

    @property
    def path(self):
        return self._ref

    def save_path(self):
        """Default path for the file to be wrotten to"""
        raise NotImplementedError()

    def exists(self, path=None):
        return exists(self.save_path(path))

    @property
    def doc(self):
        """Return the Metatab metadata document"""
        if not self._doc and self._ref:
            self._doc = MetatabDoc(TermParser(self._ref))

        return self._doc

    def copy_section(self, section_name, doc):

        for t in doc[section_name]:
            self.doc.add_term(t)

    def resources(self, name=None, term=None, section='resources'):
        for r in self.doc.resources(name, term, section=section):
            yield r

    @property
    def datafiles(self):

        for r in self.doc.resources(term=['root.datafile', 'root.suplimentarydata',
                                          'root.datadictionary']):
            yield r

    def datafile(self, ref):
        """Return a resource, as a file-like-object, given it's name or url as a reference. """

        r = list(self.doc.resources(name=ref))

        if not r:
            return None
        else:
            return r[0]

    @property
    def documentation(self):
        for t in self.doc.terms:
            if t.term_is(['root.documentation']):
                yield Resource(t, self)

    def schema(self, ref):
        """Return information about a resource, given a name or url"""
        raise NotImplementedError()

    @property
    def package_name(self):
        return self._doc.find_first_value('Root.Name')

    @property
    def sections(self):

        class _Sections(object):

            def __init__(self, doc):
                self.doc = doc

            @property
            def root(self):
                return self.doc['root']

            @property
            def resources(self):
                if not 'resources' in self.doc:
                    self.doc.get_or_new_section('Resources',
                                                "Name Schema Space Time StartLine HeaderLines Encoding Description".split())

                return self.doc['resources']

            @property
            def contacts(self):
                if not 'Contacts' in self.doc:
                    self.doc.get_or_new_section('Contacts', 'Email Org Url'.split())

                return self.doc['Contacts']

            @property
            def documentation(self):
                if not 'Documentation' in self.doc:
                    self.doc.get_or_new_section('Documentation', 'Title Schema Description '.split())

                return self.doc['documentation']

            @property
            def schema(self):
                if not 'Schema' in self.doc:
                    self.doc.get_or_new_section('Schema', 'DataType AltName Description'.split())

                return self.doc['schema']

        return _Sections(self._doc)

    @staticmethod
    def extract_path_name(ref):

        du = Url(ref)

        if du.proto == 'file':
            path = abspath(ref)
            name = basename(splitext(path)[0])
            ref = "file://" + path
        else:
            path = ref

            if du.target_segment:
                try:
                    int(du.target_segment)
                    name = du.target_file + text_type(du.target_segment)

                except ValueError:
                    name = du.target_segment

            else:
                name = splitext(du.target_file)[0]

        return ref, path, name

    @staticmethod
    def classify_url(url):

        ss = SourceSpec(url=url)

        if ss.format in ('xls', 'xlsx', 'tsv', 'csv'):
            term_name = 'DataFile'
        elif ss.format in ('pdf', 'doc', 'docx', 'html'):
            term_name = 'Documentation'
        else:
            term_name = 'Resource'

        return term_name

    @staticmethod
    def run_row_intuit(path, cache):

        for encoding in ('ascii', 'utf8', 'latin1'):
            try:
                rows = list(islice(RowGenerator(url=path, encoding=encoding, cache=cache), 5000))
                return encoding, RowIntuiter().run(list(rows))
            except TextEncodingError:
                pass

        raise Exception('Failed to convert with any encoding')

    @staticmethod
    def find_files(base_path, types):

        for root, dirs, files in walk(base_path):
            if '_metapack' in root:
                continue

            for f in files:
                if f.startswith('_'):
                    continue

                b, ext = splitext(f)
                if ext[1:] in types:
                    yield join(root, f)

    def load_declares(self):

        self.doc.load_declarations(t.value for t in self.doc.find('Root.Declare'))

    def prt(self, *args):
        if self._callback:
            self._callback(*args)

    def warn(self, *args):
        if self._callback:
            self._callback('WARN', *args)

    def err(self, *args):
        if self._callback:
            self._callback('ERROR', *args)

    def add_single_resource(self, ref, **properties):
        """ Add a single resource, without trying to enumerate it's contents
        :param ref:
        :return:
        """

        t = self.doc.find_first('Root.Datafile', value=ref)

        if t:
            self.prt("Datafile exists for '{}', deleting".format(ref))
            self.doc.remove_term(t)

        term_name = self.classify_url(ref)

        ref, path, name = self.extract_path_name(ref)

        self.prt("Adding resource for '{}'".format(ref))

        try:
            encoding, ri = self.run_row_intuit(path, self._cache)
        except Exception as e:
            self.warn("Failed to intuit '{}'; {}".format(path, e))
            return None

        if not name:

            name = sha1(slugify(path).encode('ascii')).hexdigest()[:12]

            # xlrd gets grouchy if the name doesn't start with a char
            try:
                int(name[0])
                name = 'a' + name[1:]
            except:
                pass

        if 'name' in properties:
            name = properties['name']
            del properties['name']

        return self.sections.resources.new_term(term_name, ref, name=name,
                                                startline=ri.start_line,
                                                headerlines=','.join(str(e) for e in ri.header_lines),
                                                encoding=encoding,
                                                **properties)

    def add_resource(self, ref, **properties):
        """Add one or more resources entities, from a url and property values,
        possibly adding multiple entries for an excel spreadsheet or ZIP file"""

        raise NotImplementedError("Still uses decompose_url")

        du = Bunch(decompose_url(ref))

        added = []
        if du.proto == 'file' and isdir(ref):
            for f in self.find_files(ref, ['csv']):

                if f.endswith(DEFAULT_METATAB_FILE):
                    continue

                if self._doc.find_first('Root.Datafile', value=f):
                    self.prt("Datafile exists for '{}', ignoring".format(f))
                else:
                    added.extend(self.add_resource(f, **properties))
        else:
            self.prt("Enumerating '{}'".format(ref))

            for c in enumerate_contents(ref, self._cache):
                added.append(self.add_single_resource(c.rebuild_url(), **properties))

        return added

    def _clean_doc(self, doc=None):
        """Clean the doc before writing it, removing unnecessary properties and doing other operations."""

        if doc is None:
            doc = self.doc

        resources = doc['Resources']

        # We don't need these anymore because all of the data written into the package is normalized.
        for arg in ['startline', 'headerlines', 'encoding']:
            for e in list(resources.args):
                if e.lower() == arg:
                    resources.args.remove(e)

        for term in resources:
            term['startline'] = None
            term['headerlines'] = None
            term['encoding'] = None

        schema = doc['Schema']

        ## FIXME! This is probably dangerous, because the section args are changing, but the children
        ## are not, so when these two are combined in the Term.properties() acessors, the values are off.
        ## Because of this, _clean_doc should be run immediately before writing the doc.
        for arg in ['altname', 'transform']:
            for e in list(schema.args):
                if e.lower() == arg:
                    schema.args.remove(e)

        for table in self.doc.find('Root.Table'):
            for col in table.find('Column'):
                try:
                    col.value = col['altname'].value
                except:
                    pass

                col['altname'] = None
                col['transform'] = None

        return doc

    def _load_resources(self):
        """Copy all of the Datafile entries into the package"""

        assert type(self.doc) == MetapackDoc

        for r in self.datafiles:

            if not r.url:
                self.warn("No value for URL for {} ".format(r.term))
                continue

            try:
                if self._resource.exists(r):
                    self.prt("Resource '{}' exists, skipping".format(r.name))
                continue
            except AttributeError:
                pass

            self.prt("Reading resource {} from {} ".format(r.name, r.resolved_url))

            try:
                if not r.headers:
                    raise PackageError("Resource {} does not have header. Have schemas been generated?"
                                        .format(r.name))
            except AttributeError:
                raise PackageError("Resource '{}' of type {} does not have a headers property"
                                   .format(r.url, type(r)))
            try:
                code_path = join(dirname(self.package_dir), 'row_processors', r.name + '.py')
            except AttributeError:
                # Not all packages have a package_dir property, which is an error,
                # but we really only need code_path for the FilesystemPackage
                code_path = None


            rg = self.doc.resource(r.name, env=self._env,code_path=code_path)

            assert rg is not None

            if True:
                # Skipping the first line because we'll insetrt the headers manually
                self._load_resource(r, islice(rg, 1, None), r.headers)

            else:

                # Old code; no longer sure why the code is faking the start line and removing
                # the format, headerlines, etc.

                start_line = int(r.get_value('startline')) if r.get_value('startline') is not None  else 1

                gen = islice(rg, start_line, None)

                r.encoding = None
                r.startline = None
                r.headerlines = None
                r.format = None

                self._load_resource(r, gen, r.headers)

    def _get_ref_contents(self, t):

        uv = Url(t.value)
        ur = Url(self._ref)

        # In the case that the input doc is a file, and the ref is to a file,
        # try interpreting the file as relative.
        if ur.proto == 'file' and uv.proto == 'file':
            path = uv.prefix_path(Url(ur.dirname()).parts.path)
            ss = SourceSpec(path)

        else:
            ss = SourceSpec(t.value)

        return self._download_ss(ss)

    def _download_ss(self,ss):

        try:
            d = download_and_cache(ss, self._cache)
        except DownloadError as e:
            self.warn("Failed to load file for '{}': {}".format(ss, e))
            return None, None

        dflo = get_dflo(ss, d['sys_path'])

        f = dflo.open('rb')

        try:
            # For file file, the target_file may actually be a regex, so we have to resolve the
            # regex before using it as a filename
            real_name = basename(dflo.memo[1].name)  # Internal detail of how Zip files are accessed
        except (AttributeError, TypeError):

            real_name = basename(ss.target_file)

        return real_name, f

    def _load_documentation_files(self):
        """Copy all of the Datafile entries into the Excel file"""

        for doc in self.doc.find(['Root.Documentation', 'Root.Image']):

            real_name, f = self._get_ref_contents(doc)

            if not f:
                continue

            if doc.term_is('Root.Documentation'):
                # Prefer the slugified title to the base name, because in cases of collections
                # of many data releases, like annual datasets, documentation files may all have the same name,
                # but the titles should be different.
                real_name_base, ext = splitext(real_name)

                name = doc.get_value('name') if doc.get_value('name') else real_name_base
                real_name = slugify(name) + ext

            self._load_documentation(doc, f.read(), real_name)

            f.close()

    def _load_documentation(self, term, contents):
        raise NotImplementedError()

    def _load_files(self):
        """Load other files"""

        def copy_dir(path):
            for (dr, _, files) in walk(path):
                for fn in files:

                    if '__pycache__' in fn:
                        continue

                    relpath = dr.replace(self.source_dir, '').strip('/')
                    src = join(dr, fn)
                    dest = join(relpath, fn)

                    real_name, f = self._download_ss(SourceSpec(src))

                    self._load_file( dest, f.read())


        for term in self.resources(term = 'Root.Pythonlib'):

            uv = Url(term.value)
            ur = Url(self._ref)

            # In the case that the input doc is a file, and the ref is to a file,
            # try interpreting the file as relative.
            if ur.proto == 'file' and uv.proto == 'file':

                # Either a file or a directory
                path = join(self.source_dir, uv.path())
                if isdir(path):
                    copy_dir(path)

            else:
                # Load it as a URL
                real_name, f = self._get_ref_contents(term)
                self._load_file(term.value,f.read() )

        nb_dir = join(self.source_dir, 'notebooks')

        if exists(nb_dir) and isdir(nb_dir):
            copy_dir(nb_dir)



    def _load_file(self,  filename, contents):
        raise NotImplementedError()


    def check_is_ready(self):
        pass


TableColumn = namedtuple('TableColumn', 'path name start_line header_lines columns')


def open_package(ref, cache=None, clean_cache=False):

    package_url, metadata_url = resolve_package_metadata_url(ref)

    cache = cache if cache else get_cache()

    return MetapackDoc(metadata_url, package_url=package_url, cache=cache)


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