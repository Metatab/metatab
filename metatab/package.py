# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Class for writing Metapack packages"""

import json

import six
import unicodecsv as csv
from collections import namedtuple
from io import BytesIO
from metatab import TermParser, MetatabDoc
from os import makedirs, remove
from os.path import isdir, join, dirname, exists
from rowgenerators import RowGenerator, decompose_url
from six import string_types, text_type
from .exc import PackageError
from .util import Bunch
from rowgenerators.util import get_cache


METATAB_FILE = 'metadata.csv'

TableColumn = namedtuple('TableColumn', 'path name start_line header_lines columns')


class Package(object):
    def __new__(cls, ref=None, cache=None, callback=None):

        if cls == Package:

            b = Bunch(decompose_url(ref))

            if b.file_format in ('xls', 'xlsx'):
                return super(Package, cls).__new__(ExcelPackage)
            elif b.file_format == 'zip':
                return super(Package, cls).__new__(ZipPackage)
            elif b.proto == 'gs':
                return super(Package, cls).__new__(GooglePackage)
            elif b.proto == 's3':
                return super(Package, cls).__new__(S3Package)
            elif b.file_format == 'csv':
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
            def schema(self):
                if not 'Schema' in self.doc:
                    self.doc.get_or_new_section('Schema', 'DataType AltName Description'.split())

                return self.doc['schema']

        return _Sections(self._doc)

    @staticmethod
    def extract_path_name(ref):
        from os.path import splitext, basename, abspath

        du = Bunch(decompose_url(ref))

        if du.proto == 'file':
            path = abspath(ref)
            name = basename(splitext(path)[0])
            ref = "file://" + path
        else:
            path = ref

            if du.file_segment:
                try:
                    int(du.file_segment)
                    name = du.target_file + text_type(du.file_segment)

                except ValueError:
                    name = du.file_segment

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

        du = Bunch(decompose_url(ref))

        added = []
        if du.proto == 'file' and isdir(ref):
            for f in self.find_files(ref, ['csv']):

                if f.endswith(METATAB_FILE):
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

    def _load_resources(self):
        """Copy all of the Datafile entries into the Excel file"""
        from itertools import islice
        from rowgenerators import RowGenerator

        for r in self.datafiles:

            if not r.url:
                self.warn("No value for URL for {} ".format(r.term))
                continue

            self.prt("Reading resource {} from {} ".format(r.name, r.resolved_url))

            rg = RowGenerator(url=r.resolved_url, cache=self._cache, encoding=r.get('encoding'))

            gen = islice(rg, r.get('startline'), None)

            r.encoding = None
            r.startlines = None
            r.headerlines = None
            r.format = None

            self._load_resource(r, gen)

    def _load_documentation(self):
        """Copy all of the Datafile entries into the Excel file"""

        raise NotImplementedError()



class GooglePackage(Package):
    """A Zip File package"""


class FileSystemPackage(Package):
    """A File System package"""

    """A Zip File package"""

    def __init__(self, path=None, callback=None, cache=None):

        super(FileSystemPackage, self).__init__(path, callback=callback, cache=cache)

    def save(self, path=None):

        if not self.doc.find_first_value('Root.Name'):
            raise PackageError("Package must have Root.Name term defined")

        self.sections.resources.sort_by_term()

        self.doc.cleanse()

        self.load_declares()

        self._init_dir(path)

        self._load_resources()

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
        self._doc.write_csv(join(self.package_dir, 'metatab.csv'))

    def _write_dpj(self):


        from metatab.datapackage import convert_to_datapackage

        with open(join(self.package_dir, 'datapackage.json'), 'w') as f:
            f.write(json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _load_resource(self, r, gen):

        self.prt("Loading data for '{}' ".format(r.name))

        r.url = 'data/' + r.name + '.csv'

        path = join(self.package_dir, r.url)

        makedirs(dirname(path), exist_ok=True)

        if exists(path):
            remove(path)

        with open(path, 'wb') as f:
            w = csv.writer(f)
            w.writerows(gen)


class SocrataPackage(Package):
    """"""


class CkanPackage(Package):
    """"""


class CsvPackage(Package):
    """"""

    def save(self, path=None):

        self.doc.cleanse()

        self.load_declares()

        if path and isdir(path):
            _path = join(self.path, self.doc.find_first_value('Root.Name') + ".csv")

        elif path:
            _path = path

        else:
            _path = self.doc.find_first_value('Root.Name') + ".csv"

        assert _path

        self.doc.write_csv(_path)


class ExcelPackage(Package):
    """An Excel File Package"""

    def __init__(self, path=None, callback=None, cache=None):

        super(ExcelPackage, self).__init__(path, callback=callback, cache=cache)

    def save(self, path=None):
        from openpyxl import Workbook
        from os.path import isdir, join

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

        for row in self.doc.rows:
            meta_ws.append(row)

        if path and isdir(path):
            self.wb.save(join(path, self.doc.find_first_value('Root.Name') + ".xlsx"))

        elif path:
            self.wb.save(path)

        else:
            self.wb.save(self.doc.find_first_value('Root.Name') + ".xlsx")

    def _load_resource(self, r, gen):

        self.prt("Loading data for sheet '{}' ".format(r.name))

        ws = self.wb.create_sheet(r.name)

        r.url = r.name

        # table = self.doc.find_first('Root.Table', r.name)
        # ws.append([ c.value for c in table.children if c.term_is('table.column')])

        for row in gen:
            ws.append(row)


class ZipPackage(Package):
    """A Zip File package"""

    def __init__(self, path=None, callback=None, cache=None):

        super(ZipPackage, self).__init__(path, callback=callback, cache=cache)

    def save(self, path=None):

        if not self.doc.find_first_value('Root.Name'):
            raise PackageError("Package must have Root.Name term defined")

        self.sections.resources.sort_by_term()

        self.load_declares()

        self.doc.cleanse()

        self._init_zf(path)

        self._load_resources()

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
            self.warn(("Error while writing datapackage.json. Skipping: "+str(e)))
            return

        self.zf.writestr(self.package_name + '/datapackage.json',json.dumps(dpj, indent=4))

    def _load_resource(self, r, gen):

        self.prt("Loading data for '{}'  from '{}'".format(r.name, r.resolved_url))

        bio = BytesIO()
        writer = csv.writer(bio)

        writer.writerows(gen)

        r.url = 'data/' + r.name + '.csv'

        self.zf.writestr(self.package_name + '/' + r.url, bio.getvalue())

class S3Package(Package):
    """A Zip File package"""

    def __init__(self, path=None, callback=None, cache=None):

        super(S3Package, self).__init__(path, callback=callback, cache=cache)

    def save(self, url):

        name = self.doc.find_first_value('Root.Name')

        if not name:
            raise PackageError("Package must have Root.Name term defined")

        self.prt("Preparing S3 package '{}' ".format(name))

        self.sections.resources.sort_by_term()

        self.doc.cleanse()

        self.load_declares()

        self._init_s3(url)

        self._load_resources()

        self._write_doc()

        self._write_dpj()

        self.close()

        return self

    def _init_s3(self, url):
        from rowgenerators import Url
        from rowgenerators import parse_url_to_dict
        import boto3

        p = parse_url_to_dict(url)

        self._s3 = boto3.resource('s3')

        self._bucket = self._s3.Bucket(p['netloc'])
        self._prefix = p['path']

    def close(self):
        pass

    def write_to_s3(self, path, body):

        key = join(self._prefix, self.package_name, path).strip('/')

        return self._bucket.put_object(Key=key, Body=body, ACL='public-read')

    def _write_doc(self):

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerows(self.doc.rows)

        self.write_to_s3('metadata.csv', bio.getvalue())

    def _write_dpj(self):
        from metatab.datapackage import convert_to_datapackage

        self.write_to_s3('datapackage.json', json.dumps(convert_to_datapackage(self._doc), indent=4))

    def _load_resource(self, r, gen):

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerows(gen)

        r.url = 'data/' + r.name + '.csv'

        data = bio.getvalue()

        self.prt("Loading data ({} bytes) to '{}' ".format(len(data),r.url))

        self.write_to_s3(r.url, data)
