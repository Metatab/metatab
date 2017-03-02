# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""Class for writing Metapack packages"""

import json
from collections import namedtuple
from io import BytesIO
from os import makedirs, remove
from os.path import isdir, join, dirname, exists

import unicodecsv as csv
from six import string_types, text_type

from metatab import TermParser, MetatabDoc, DEFAULT_METATAB_FILE, Resource
from rowgenerators import Url
from rowgenerators.util import get_cache
from .exc import PackageError
from .util import Bunch
from metatab.datapackage import convert_to_datapackage

TableColumn = namedtuple('TableColumn', 'path name start_line header_lines columns')


class Package(object):
    def __new__(cls, ref=None, cache=None, callback=None):

        if cls == Package:

            b = Bunch(Url(ref).dict)

            if b.target_format in ('xls', 'xlsx'):
                return super(Package, cls).__new__(ExcelPackage)
            elif b.target_format == 'zip':
                return super(Package, cls).__new__(ZipPackage)
            elif b.proto == 'gs':
                return super(Package, cls).__new__(GooglePackage)
            elif b.proto == 's3':
                return super(Package, cls).__new__(S3Package)
            elif b.target_format == 'csv':
                return super(Package, cls).__new__(CsvPackage)
            else:
                raise PackageError("Can't determine package type for ref '{}' ".format(ref))

        else:
            return super(Package, cls).__new__(cls)

    def __init__(self, ref=None, cache=None, callback=None):

        self._cache = cache if cache else get_cache('metapack')
        self._ref = ref
        self._doc = None
        self._callback = callback

        self.init_doc()

    def load_doc(self, ref):

        if isinstance(ref, string_types):
            self._doc = MetatabDoc(ref, cache=self._cache)
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

    @property
    def doc(self):
        """Return the Metatab metadata document"""
        if not self._doc and self._ref:
            self._doc = MetatabDoc(TermParser(self._ref))

        return self._doc

    def copy_section(self, section_name, doc):

        for t in doc[section_name]:
            self.doc.add_term(t)

    @property
    def resources(self):
        for r in self.doc.resources():
            yield r

    @property
    def datafiles(self):

        for r in self.doc.resources(term=['root.datafile', 'root.suplimentarydata', 'root.datadictionary']):
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
                    self.doc.get_or_new_section('Documentation', 'Name  Schema Space Time Title Description '.split())

                return self.doc['documentation']

            @property
            def identity(self):
                if not 'Identity' in self.doc:
                    self.doc.get_or_new_section('Documentation', 'Code'.split())

                return self.doc['identity']

            @property
            def schema(self):
                if not 'Schema' in self.doc:
                    self.doc.get_or_new_section('Schema', 'DataType AltName Description'.split())

                return self.doc['schema']

        return _Sections(self._doc)

    @staticmethod
    def extract_path_name(ref):
        from os.path import splitext, basename, abspath

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
        from rowgenerators import SourceSpec

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
        from rowgenerators import RowGenerator
        from tableintuit import RowIntuiter
        from itertools import islice
        from rowgenerators import TextEncodingError

        for encoding in ('ascii', 'utf8', 'latin1'):
            try:
                rows = list(islice(RowGenerator(url=path, encoding=encoding, cache=cache), 5000))
                return encoding, RowIntuiter().run(list(rows))
            except TextEncodingError:
                pass

        raise Exception('Failed to convert with any encoding')

    @staticmethod
    def find_files(base_path, types):
        from os import walk
        from os.path import join, splitext

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
        from metatab.util import slugify

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
            from hashlib import sha1
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
        from rowgenerators import enumerate_contents
        from os.path import isdir

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

    def _clean_doc(self):
        """Clean the doc before writing it, removing unnecessary properties and doing other operations."""

        resources = self.doc['Resources']

        for arg in [ 'startline', 'headerlines', 'encoding']:
            for e in list(resources.args):
                if e.lower() == arg:
                    resources.args.remove(e)

        schema = self.doc['Schema']

        for arg in [ 'altname', 'transform' ]:
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

    def _load_resources(self):
        """Copy all of the Datafile entries into the Excel file"""
        from itertools import islice
        from rowgenerators import RowGenerator

        for r in self.datafiles:

            if not r.url:
                self.warn("No value for URL for {} ".format(r.term))
                continue

            self.prt("Reading resource {} from {} ".format(r.name, r.resolved_url))

            assert r.properties.get('encoding') == r.get('encoding') or  \
                   bool(r.properties.get('encoding'))==bool(r.get('encoding')),\
                   (r.properties.get('encoding'),r.get('encoding'))

            rg = RowGenerator(url=r.resolved_url,
                              name=r.get('name'),
                              encoding=r.get('encoding'),
                              target_format=r.get('format'),
                              target_file=r.get('file'),
                              target_segment=r.get('segment'),
                              cache=self._cache)

            start_line = int(r.get('startline')) if r.get('startline') is not None  else 1

            gen = islice(rg, start_line, None)

            r.encoding = None
            r.startline = None
            r.headerlines = None
            r.format = None

            if not r.headers():
                raise PackageError("Resource {} does not have header. Have schemas been generated?".format(r.name))

            self._load_resource(r, gen, r.headers())

    def _load_documentation(self):
        """Copy all of the Datafile entries into the Excel file"""

        raise NotImplementedError()

    def check_is_ready(self):
        pass

class GooglePackage(Package):
    """A Zip File package"""


class FileSystemPackage(Package):
    """A File System package"""

    """A Zip File package"""

    def __init__(self, path=None, callback=None, cache=None):

        super(FileSystemPackage, self).__init__(path, callback=callback, cache=cache)

    def save(self, path=None):

        self.check_is_ready()

        if not self.doc.find_first_value('Root.Name'):
            raise PackageError("Package must have Root.Name term defined")

        self.sections.resources.sort_by_term()

        self.doc.cleanse()

        self.load_declares()

        self._init_dir(path)

        self._load_resources()

        self._clean_doc()

        self._write_doc()

        self._write_dpj()


        return self

    def _init_dir(self, path=None):
        from os import getcwd

        if path is None:
            path = getcwd()

        name = self.doc.find_first_value('Root.Name')

        np = join(path, name)

        if isdir(np):
            import shutil
            shutil.rmtree(np)

        makedirs(np)

        self.package_dir = np

    def _write_doc(self):
        self._doc.write_csv(join(self.package_dir, DEFAULT_METATAB_FILE))

    def _write_dpj(self):

        with open(join(self.package_dir, 'datapackage.json'), 'w') as f:
            f.write(json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _load_resource(self, r, gen, headers):

        self.prt("Loading data for '{}' ".format(r.name))

        r.url = 'data/' + r.name + '.csv'

        path = join(self.package_dir, r.url)

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)

        with open(path, 'wb') as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(gen)


class SocrataPackage(Package):
    """"""


class CkanPackage(Package):
    """"""


class CsvPackage(Package):
    """"""

    def save(self, path=None):

        self.check_is_ready()

        self.doc.cleanse()

        self.load_declares()

        if path and isdir(path):
            _path = join(self.path, self.doc.find_first_value('Root.Name') + ".csv")

        elif path:
            _path = path

        else:
            _path = self.doc.find_first_value('Root.Name') + ".csv"

        assert _path

        self._clean_doc()

        self.doc.write_csv(_path)


class ExcelPackage(Package):
    """An Excel File Package"""

    def __init__(self, path=None, callback=None, cache=None):

        super(ExcelPackage, self).__init__(path, callback=callback, cache=cache)

    def save(self, path=None):
        from openpyxl import Workbook
        from os.path import isdir, join

        self.check_is_ready()

        self.wb = Workbook(write_only=True)

        meta_ws = self.wb.create_sheet()
        meta_ws.title = "meta"
        meta_ws.sheet_properties.tabColor = "8888ff"

        if not self.doc.find_first_value('Root.Name'):
            raise PackageError("Package must have Root.Name term defined")

        self.sections.resources.sort_by_term()

        self.load_declares()

        self.doc.cleanse()

        self._load_resources()

        self._clean_doc()

        for row in self.doc.rows:
            meta_ws.append(row)

        if path and isdir(path):
            self.wb.save(join(path, self.doc.find_first_value('Root.Name') + ".xlsx"))

        elif path:
            self.wb.save(path)

        else:
            self.wb.save(self.doc.find_first_value('Root.Name') + ".xlsx")

    def _load_resource(self, r, gen, headers):

        self.prt("Loading data for sheet '{}' ".format(r.name))

        ws = self.wb.create_sheet(r.name)

        r.url = r.name

        # table = self.doc.find_first('Root.Table', r.name)
        # ws.append([ c.value for c in table.children if c.term_is('table.column')])

        ws.append(headers)

        for row in gen:
            ws.append(row)


class ZipPackage(Package):
    """A Zip File package"""

    def __init__(self, path=None, callback=None, cache=None):

        super(ZipPackage, self).__init__(path, callback=callback, cache=cache)

    def save(self, path=None):

        self.check_is_ready()

        if not self.doc.find_first_value('Root.Name'):
            raise PackageError("Package must have Root.Name term defined")

        self.sections.resources.sort_by_term()

        self.load_declares()

        self.doc.cleanse()

        self._init_zf(path)

        self._load_resources()

        self._clean_doc()

        self._write_doc()

        self._write_dpj()

        self.close()

        return self

    def _init_zf(self, path):

        from zipfile import ZipFile

        name = self.doc.find_first_value('Root.Name')

        if path and isdir(path):
            zf_path = join(path, name + ".zip")

        elif path:
            zf_path = path

        else:
            zf_path = name + ".zip"

        self.zf = ZipFile(zf_path, 'w')

    def close(self):
        if self.zf:
            self.zf.close()

    def _write_doc(self):

        bio = BytesIO()
        writer = csv.writer(bio)

        writer.writerows(self.doc.rows)

        self.zf.writestr(self.package_name + '/metadata.csv', bio.getvalue())

    def _write_dpj(self):
        from metatab.datapackage import convert_to_datapackage
        from metatab import ConversionError

        try:
            dpj = convert_to_datapackage(self._doc)
        except ConversionError as e:
            self.warn(("Error while writing datapackage.json. Skipping: " + str(e)))
            return

        self.zf.writestr(self.package_name + '/datapackage.json', json.dumps(dpj, indent=4))

    def _load_resource(self, r, gen, headers):

        self.prt("Loading data for '{}'  from '{}'".format(r.name, r.resolved_url))

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerow(headers)
        writer.writerows(gen)

        r.url = 'data/' + r.name + '.csv'

        self.zf.writestr(self.package_name + '/' + r.url, bio.getvalue())


class S3Package(Package):
    """A Zip File package"""

    def __init__(self, path=None, callback=None, cache=None):

        super(S3Package, self).__init__(path, callback=callback, cache=cache)

    def save(self, url):

        self.check_is_ready()

        name = self.doc.find_first_value('Root.Name')

        if not name:
            raise PackageError("Package must have Root.Name term defined")

        self.prt("Preparing S3 package '{}' ".format(name))

        self.sections.resources.sort_by_term()

        self.doc.cleanse()

        self.load_declares()

        self._init_s3(url)

        self._load_resources()

        self._clean_doc()

        self._write_doc()

        self._write_dpj()

        self.close()

        return self

    def _init_s3(self, url):
        from rowgenerators import parse_url_to_dict
        import boto3

        self._s3 = boto3.resource('s3')

        p = parse_url_to_dict(url)

        if p['netloc']:  # The URL didn't have the '//'
            self._prefix = p['path']
            bucket_name = p['netloc']
        else:
            proto, netpath = url.split(':')
            bucket_name, self._prefix = netpath.split('/', 1)

        self._bucket = self._s3.Bucket(bucket_name)

    def close(self):
        pass

    def write_to_s3(self, path, body):
        from botocore.exceptions import ClientError

        key = join(self._prefix, self.package_name, path).strip('/')

        try:
            o = self._bucket.Object(key)
            if o.content_length == len(body):
                self.prt("File '{}' already in bucket; skipping".format(path))
                return
            else:
                self.prt("File '{}' already in bucket, but length is different; re-wirtting".format(path))


        except ClientError as e:
            if int(e.response['Error']['Code']) != 404:
                raise


        try:
            return self._bucket.put_object(Key=key, Body=body, ACL='public-read')
        except Exception as e:
            self.err("Failed to write '{}': {}".format(path, e))

    def _write_doc(self):

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerows(self.doc.rows)

        self.write_to_s3('metadata.csv', bio.getvalue())

    def _write_dpj(self):

        self.write_to_s3('datapackage.json', json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _load_resource(self, r, gen, headers):

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerow(headers)
        writer.writerows(gen)

        r.url = 'data/' + r.name + '.csv'

        data = bio.getvalue()

        self.prt("Loading data ({} bytes) to '{}' ".format(len(data), r.url))

        self.write_to_s3(r.url, data)
