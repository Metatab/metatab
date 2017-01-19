# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
A Class for writing Zip packages in Metatab package format.
"""

from itertools import islice

import unicodecsv as csv
from fs.opener import fsopendir
from io import BytesIO
from os import makedirs
from os.path import splitext, basename, abspath, isdir, exists, join
import json
from rowgenerators import RowGenerator
from rowgenerators.util import parse_url_to_dict
from .exc import GenerateError
from .util import slugify


class ZipPackage(object):
    def __init__(self,  path, cache):
        """

        :param doc: Input Mettab document
        :param path: Path, a filename or directory, for the output zip archive
        :param cache:
        :return:
        """

        self.cache = cache
        self.path = path
        self.zf = None
        self.resources = None
        self.schema = None


    def __del__(self):
        self.close()

    def run(self, doc):

        self.package_name = slugify(self._init_doc(doc))
        self._init_zf(self.path)

        self._copy_resources(doc)
        self._write_doc()

        self._write_dpj(doc)

        return self

    def close(self):
        if self.zf:
            self.zf.close()

    def _write_doc(self):

        bio = BytesIO()
        writer = csv.writer(bio)

        writer.writerows(self.doc.rows)

        self.zf.writestr(self.package_name+'/metadata.csv', bio.getvalue())


    def _copy_section(self, section_name, doc):

        for t in doc[section_name]:
            self.doc.add_term(t)

    def _init_zf(self, path):

        from zipfile import ZipFile

        if not exists(path):
            makedirs(path)

        name = self.doc.find_first_value('root.name')

        if isdir(path):
            self.path = join(path, slugify(name) + '.zip')
        else:
            self.path = path

        self.zf = ZipFile(self.path, 'w')

    def _init_doc(self, in_doc, callback=None, cache=None):
        from . import MetatabDoc

        name = in_doc.find_first_value('root.name')

        if not name:
            raise GenerateError("Input metadata must define a package name in the Root.Name term")

        self.doc = MetatabDoc()

        self.resources = self.doc.get_or_new_section('Resources', ['Description'])

        self.schema = self.doc.get_or_new_section('Schema',
                                                  ['DataType', 'AltName', 'Description'])

        self._copy_section('root', in_doc)

        return name


    def _copy_resources(self, in_doc, callback=None, cache=None):

        table_schemas = {t.value: t.as_dict()['column'] for t in in_doc['schema']}
        file_resources = [fr.properties for fr in in_doc['resources'] if fr.term_is('root.datafile')]

        if len(table_schemas) == 0:
            raise GenerateError("Cant create package without table schemas")

        for resource in file_resources:
            if callback:
                callback("Processing {}".format(resource['name']))
            try:
                columns = table_schemas[resource['name']]
            except KeyError:
                if callback:
                    callback("WARN: Didn't get schema for table '{}', skipping".format(resource['name']))
                continue

            self._add_data_file(resource['url'], resource['name'], resource.get('description'),
                                columns, int(resource.get('startline') if resource.get('startline') else 1),
                                resource.get('encoding', 'latin1'),
                                cache=cache)


    def _add_data_file(self, ref, name, description, columns, start_line, encoding='latin1', cache=None):

        package_path = 'data/'+name+'.csv'

        self.resources.new_term('Datafile', package_path, description=description)

        if cache is None:
            cache = fsopendir('/tmp')

        bio = BytesIO()
        writer = csv.writer(bio)

        table = self.schema.new_term('Table', name)

        ref, path, name = self._extract_path_name(ref)

        for c in columns:
            table.new_child('Column', c['name'], datatype=c['datatype'],
                            altname=c.get('altname'), description=c.get('description'))

        gen = islice(RowGenerator(url=ref, cache=cache, encoding=encoding), start_line, None)

        writer.writerow([c['name'] for c in columns])
        writer.writerows(gen)

        self.zf.writestr(self.package_name+'/'+package_path, bio.getvalue())


    @staticmethod
    def _extract_path_name(ref):

        uparts = parse_url_to_dict(ref)

        if not uparts['scheme']:
            path = abspath(ref)
            name = basename(splitext(path)[0])
            ref = "file://" + path
        else:
            path = ref
            name = basename(splitext(uparts['path'])[0])

        return ref, path, name

    def _write_dpj(self, doc):
        from .datapackage import  convert_to_datapackage

        self.zf.writestr(self.package_name + '/datapackage.json', json.dumps(convert_to_datapackage(doc), indent=4))

