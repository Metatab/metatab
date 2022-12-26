# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE.txt

""" """
from rowgenerators import Source
from rowgenerators.source import Source
from rowgenerators import SourceError

class YamlMetatabSource(Source):
    """Turn a metatab-formated YAML file into Metatab rows."""

    def __init__(self, ref, table=None, cache=None, working_dir=None, env=None, **kwargs):
        super().__init__(ref, cache, working_dir, **kwargs)

        self.url = ref
        self.section_map = {}
        self.sections = {}

    def yield_dict(self, doc, d, parent=None):

        for k, v in d.items():

            tn = "{}.{}".format((parent or 'Root').split('.')[-1], k).lower()
            t = doc.decl_terms.get(tn,{})
            vtn = t.get('termvaluename','').lower()

            if isinstance(v, list):
                for e in v:
                    try:
                        value = e[vtn]
                        del e[vtn]
                        yield (tn, value, parent)
                    except KeyError:
                        pass

                    yield from self.yield_dict(doc, e, tn)
            elif isinstance(v, dict):
                yield from self.yield_dict(doc, v, tn)
            else:
                yield (tn,v, parent)


    def __iter__(self):
        """Iterate over all of the lines in the file"""

        import yaml
        from metatab import MetatabDoc

        with open(self.url.fspath) as f:
            d = yaml.load(f)

        decl = d.get('declare', 'metatab-latest')

        doc = MetatabDoc(decl=decl)

        #yield from doc.rows

        section_names = ['root','contacts','documentation','resources','references','schema']

        for section_name in section_names:
            section =  doc.decl_sections[section_name]
            #print(section_name, section)

            for tn in  section.get('terms',[]):
                self.section_map[tn.lower()] = section_name

            self.sections[section_name] = doc.get_or_new_section(section_name, section['args'])

        last_section = None
        last_term = { }
        for term_name, value, parent in self.yield_dict(doc, d):

            print(term_name, value, parent)

            section = self.sections.get(self.section_map.get(term_name) or 'root')

            if parent is None:
                term = section.new_term(term_name, value)
            else:

                parent_term = last_term[parent]
                term = parent_term.new_child(term_name, value)

            last_term[term_name] = term




        yield from doc.rows


class MetatabRowGenerator(Source):
    """An object that generates rows. The current implementation mostly just a wrapper around
    csv.reader, but it adds a path property so term interperters know where the terms are coming from
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
    """Return lines of text of a line-oriented metatab file, breaking them to be used as Metatab rows.
    This is the core of the Lines format implementation"""

    def __init__(self, ref, cache=None, working_dir=None, path = None, **kwargs):
        super().__init__(ref, cache, working_dir, path, **kwargs)

        while True:

            try:
                # Pathlib Path
                with ref.open() as r:
                    text = r.read()
                break
            except:
                pass

            try:
                # Filehandle
                text = ref.read()
                break
            except:
                pass

            try:
                # Url
                with ref.inner.fspath.open() as f:
                    text = f.read()
                break
            except:

                pass

            try:
                # File name
                with open(ref) as r:
                    text = r.read()
                break
            except:
                pass

            try:
                text = ref
                text.splitlines()
                break
            except AttributeError:
                pass


            raise SourceError("Can't handle ref of type {}".format(type(ref)))

        self._text = text
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

            # Special handling for ====, which implies a section:
            #   ==== Schema
            # is also
            #   Section: Schema

            if row.startswith('===='):
                row = re.sub(r'^=*','Section:', row)

            row = [e.strip() for e in row.split(':', 1)]

            # Pipe characters seperate columns
            if len(row) > 1:
                row = [row[0]] + [ e.replace('\|','|') for e in re.split(r'(?<!\\)\|', row[1]) ]

            yield row