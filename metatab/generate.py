# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Generate rows from a variety of paths, references or other input
"""

from .exc import IncludeError, GenerateError


def generateRows(ref, cache=None):

    from inspect import isgenerator
    from six import string_types

    if isinstance(ref, (list,tuple)):
        rg = MetatabRowGenerator(ref)
    elif isgenerator(ref):
        rg = MetatabRowGenerator(ref)
    elif isinstance(ref, string_types):
        rg = GenericRowGenerator(ref, cache=cache)
    else:
        raise GenerateError("Cant figure out how to generate rows from ref: "+str(ref))

    return rg

class MetatabRowGenerator(object):
    """An object that generates rows. The current implementation mostly just a wrapper around
    csv.reader, but it add a path property so term interperters know where the terms are coming from
    """

    def __init__(self, rows, path=None):
        self._rows = rows
        self._path = path or '<none>'

    @property
    def path(self):
        return self._path

    def open(self):
        pass

    def close(self):
        pass

    def __iter__(self):
        for row in self._rows:
            yield row

# FIXME: Can probably remove this class in favor of GenericRowGenerator
class CsvUrlRowGenerator(MetatabRowGenerator):
    """An object that generates rows. The current implementation mostly just a wrapper around
    csv.reader, but it add a path property so term interperters know where the terms are coming from
    """

    def __init__(self, url):

        self._url = url
        self._f = None

    @property
    def path(self):
        return self._url

    def open(self):
        import sys

        import six.moves.urllib as urllib
        try:
            if sys.version_info[0] < 3:
                self._f = urllib.request.urlopen(self._url)
            else:
                self._f = urllib.request.urlopen(self._url)

        except urllib.error.URLError:
            raise IncludeError("Failed to find file by url: {}".format(self._url))

    def close(self):
        pass

    def __iter__(self):
        import unicodecsv as csv

        self.open()

        # Python 3, should use yield from
        for row in csv.reader(self._f):
            yield row

        self.close()

# FIXME: Can probably remove this class in favor of GenericRowGenerator
class CsvPathRowGenerator(MetatabRowGenerator):
    """An object that generates rows. The current implementation mostly just a wrapper around
    csv.reader, but it add a path property so term interperters know where the terms are coming from
    """

    def __init__(self, path):

        self._path = path
        self._f = None

    @property
    def path(self):
        return self._path

    def open(self):
        import sys

        from os.path import join

        try:

            if sys.version_info[0] < 3:
                self._f = open(self._path, 'rb')
            else:
                self._f = open(self._path, 'rb')  # 'b' because were using unicodecsv

        except IOError:
            raise IncludeError("Failed to find file: {}".format(self._path))

    def close(self):

        if self._f:
            self._f.close()
            self._f = None

    def __iter__(self):
        import unicodecsv as csv

        self.open()

        # Python 3, should use yield from
        for row in csv.reader(self._f):
            yield row

        self.close()

# FIXME: Can probably remove this class in favor of GenericRowGenerator
class CsvDataRowGenerator(MetatabRowGenerator):
    """Generate rows from CSV data, as a string
    """

    def __init__(self, data, path=None):
        self._data = data
        self._path = path or '<none>'

    @property
    def path(self):
        return self._path

    def open(self):
        pass

    def close(self):
        pass

    def __iter__(self):
        import unicodecsv as csv
        from io import BytesIO

        f = BytesIO(self._data)

        # Python 3, should use yield from
        for row in csv.reader(f):
            yield row

class GenericRowGenerator(MetatabRowGenerator):
    """Use generators from the rowgenerator package"""

    def __init__(self, url, cache=None):
        self._url = url
        self._cache = cache

    @property
    def path(self):
        return self._url

    def open(self):
        pass

    def close(self):
        pass

    def __iter__(self):

        from rowgenerators import SourceSpec

        spec = SourceSpec(url=self._url)


        for row in spec.get_generator(self._cache):
            yield row

class TextRowGenerator(MetatabRowGenerator):
    """Return lines of text of a line-oriented metatab file, breaking them to be used as Metatab rows"""


    def __init__(self, ref, path=None):


        while True:

            text = None

            try:
                with open(ref) as r:
                    text = r.read()
                break
            except:
                pass

            try:
                with ref.open() as r:
                    text = r.read()
                break
            except:
                pass

            try:
                text = ref.read()
                break
            except:
                pass


            text = ref
            break

        self._text_lines = text.splitlines()
        self._path = path or '<none>'

    @property
    def path(self):
        return self._path

    def open(self):
        pass

    def close(self):
        pass

    def __iter__(self):
        import re

        for row in self._text_lines:
            if re.match(r'^\s*#', row): # Skip comments
                continue
            yield [e.strip() for e in row.split(':',1)]


