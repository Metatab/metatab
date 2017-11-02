
# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from rowgenerators import Source

class MetatabRowGenerator(Source):
    """An object that generates rows. The current implementation mostly just a wrapper around
    csv.reader, but it add a path property so term interperters know where the terms are coming from
    """

    def __init__(self, ref, cache=None, working_dir=None, path = None, **kwargs):
        super().__init__(ref, cache, working_dir, **kwargs)

        self._rows = ref
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



class TextRowGenerator(MetatabRowGenerator):
    """Return lines of text of a line-oriented metatab file, breaking them to be used as Metatab rows"""

    def __init__(self, ref, cache=None, working_dir=None, path = None, **kwargs):
        super().__init__(ref, cache, working_dir, path, **kwargs)

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
            if re.match(r'^\s*#', row):  # Skip comments
                continue

            # Special handling for ===, which implies a section:
            #   ==== Schema
            # is also
            #   Section: Schema

            if row.startswith('===='):
                row = re.sub(r'^=*','Section:', row)

            row = [e.strip() for e in row.split(':', 1)]

            yield row


