# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Parser for the Simple Data Package format. The parser consists of several iterable generator
objects.

"""

NO_TERM = '<no_term>'  # No parent term -- no '.' --  in term cell
ELIDED_TERM = '<elided_term>'  # A '.' in term cell, but no term before it.


class ParserError(Exception):
    def __init__(self, *args, **kwargs):
        super(ParserError, self).__init__(*args, **kwargs)
        self.term = None


class IncludeError(ParserError):
    pass


class Term(object):
    """Parses a row into the parts of a term

        Public attributes. These are set externally to the constructor.

        file_name Filename or URL of faile that contains term
        row: Row number of term
        col Column number of term
        is_arg_child Term was generated from arguments of parent
        child_property_type What datatype to use in dict conversion
        valid Did term pass validation tests? Usually based on DeclaredTerm values.

    """

    def __init__(self, term, value, term_args=[],
                 row=None, col=None, file_name=None,
                 is_arg_child=None):
        """

        :param term: Simple or compoint term name
        :param value: Term value, from second column of spreadsheet
        :param term_args: Colums 2+ from term row


        """

        def strip_if_str(v):
            try:
                return v.strip()
            except AttributeError:
                return v

        self.parent_term, self.record_term = Term.split_term_lower(term)

        self.value = strip_if_str(value) if value else None
        self.args = [strip_if_str(x) for x in term_args]

        self.section = None  # Name of section the term is in.

        self.file_name = file_name
        self.row = row
        self.col = col

        # When converting to a dict, what dict to to use for the self.value value
        self.term_value_name = '@value'  # May be change in term parsing

        # When converting to a dict, what datatype should be used for this term.
        # Can be forced to list, scalar, dict or other types.
        self.child_property_type = 'any'
        self.valid = None

        self.is_arg_child = is_arg_child  # If true, term was

        self.children = []  # WHen terms are linked, hold term's children.

    @classmethod
    def split_term(cls, term):
        """
        Split a term in to parent and record term components
        :param term: combined term text
        :return: Tuple of parent and record term
        """
        if '.' in term:
            parent_term, record_term = term.split('.')
            parent_term, record_term = parent_term.strip(), record_term.strip()

            if parent_term == '':
                parent_term = ELIDED_TERM

        else:
            parent_term, record_term = NO_TERM, term.strip()

        return parent_term, record_term

    @classmethod
    def split_term_lower(cls, term):
        """
        Like split_term, but also lowercases both parent and record term
        :param term: combined term text
        :return: Tuple of parent and record term

        """

        return tuple(e.lower() for e in Term.split_term(term))

    def file_ref(self):
        """Return a string for the file, row and column of the term."""
        if self.file_name is not None and self.row is not None:
            return "{} {}:{} ".format(self.file_name, self.row, self.col)
        elif self.row is not None:
            return " {}:{} ".format(self.row, self.col)
        else:
            return ''

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):
        return "<Term: {}{}.{} {} {} >".format(self.file_ref(), self.parent_term,
                                               self.record_term, self.value, self.args)

    def __str__(self):
        if self.parent_term == NO_TERM:
            return "{}{}: {}".format(self.file_ref(), self.record_term, self.value)

        elif self.parent_term == ELIDED_TERM:
            return "{}.{}: {}".format(self.file_ref(), self.record_term, self.value)

        else:
            return "{}{}.{}: {}".format(self.file_ref(), self.parent_term, self.record_term, self.value)


class CsvPathRowGenerator(object):
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

        if self._path.startswith('http'):
            import urllib2
            try:
                f = urllib2.urlopen(self._path)
            except urllib2.URLError:
                raise IncludeError("Failed to find file by url: {}".format(self._path))

            f.name = self._path  # to be symmetric with files.
        else:
            from os.path import join

            try:
                f = open(self._path)
            except IOError:
                raise IncludeError("Failed to find file: {}".format(self._path))

        self._f = f

    def close(self):

        if self._f:
            self._f.close()
            self._f = None

    def __iter__(self):
        import csv
        self.open()

        # Python 3, should use yield from
        for row in csv.reader(self._f):
            yield row

        self.close()


class CsvDataRowGenerator(object):
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
        import csv
        from cStringIO import StringIO

        f = StringIO(self._data)

        # Python 3, should use yield from
        for row in csv.reader(f):
            yield row


class RowGenerator(object):
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


class TermGenerator(object):
    """Generate terms from a row generator. It will produce a term for each row, and child
    terms for any arguments to the row. """

    def __init__(self, row_gen):
        """

        :param row_gen: an interator that generates rows
        :return:
        """

        from os.path import dirname, basename

        self._row_gen = row_gen

        self._path = self._row_gen.path

    def __iter__(self):
        """An interator that generates term objects"""
        from os.path import dirname, join

        for line_n, row in enumerate(self._row_gen, 1):

            if not row[0].strip() or row[0].strip().startswith('#'):
                continue

            t = Term(row[0].lower(),
                     row[1] if len(row) > 1 else '',
                     row[2:] if len(row) > 2 else [],
                     row=line_n,
                     col=1,
                     file_name=self._path)

            if t.record_term.lower() == 'include':

                yield t

                if not self._path:
                    raise ParserError("Can't include because don't know current path"
                                      .format(self._root_directory))

                include_ref = t.value.strip('/')

                if include_ref.startswith('http'):
                    path = include_ref
                else:
                    path = join(dirname(self._path), include_ref)

                for t in TermGenerator(CsvPathRowGenerator(path)):
                    yield t

                continue  # Already yielded the include term

            yield t

            # Yield any child terms, from the term row arguments
            if t.record_term.lower() != 'section':
                for col, value in enumerate(t.args, 0):
                    if str(value).strip():
                        yield Term(t.record_term.lower() + '.' + str(col), str(value), [],
                                   row=line_n,
                                   col=col + 2,  # The 0th argument starts in col 2
                                   file_name=self._path,
                                   is_arg_child=True)


class TermInterpreter(object):
    """Takes a stream of terms and sets the parameter map, valid term names, etc """

    def __init__(self, term_gen, remove_special=True):
        """
        :param term_gen: an an iterator that generates terms
        :param remove_special: If true ( default ) remove the special terms from the stream
        :return:
        """

        from collections import defaultdict

        self._remove_special = remove_special

        self._term_gen = term_gen

        self._param_map = []  # Current parameter map, the args of the last Section term

        # _sections and _terms are loaded from Declare documents, in
        # handle_declare and import_declare_doc. The Declare doc information
        # can also be loaded before parsing, so the Declare term can be eliminated.
        self._sections = {}  # Declared sections and their arguments
        self._terms = {}  # Pre-defined terms, plus TermValueName and ChildPropertyType

        self.errors = []

    @property
    def sections(self):
        return self._sections

    @property
    def synonyms(self):
        return {k: v['synonym'] for k, v in self._terms.items() if 'synonym' in v}

    @property
    def terms(self):
        return self._terms

    @property
    def declare_dict(self):
        return {
            'sections': self.sections,
            'terms': self.terms,
        }

    def as_dict(self):
        """Iterate, link terms and convert to a dict"""

        return self.convert_to_dict(self.link_terms())

    def link_terms(self):
        """Return a heirarchy of records from a stream of terms

        NOTE: This method will iterate over self.

        :param term_generator:
        """

        root = Term('Root', None)
        last_term_map = {NO_TERM: root}

        for term in self:

            try:
                parent = last_term_map[term.parent_term]
            except KeyError as e:

                raise ParserError("Failed to find parent term in last term map: {} {} \nTerm: \n{}"
                                  .format(e.__class__.__name__, e, term))

            parent.add_child(term)

            if not term.is_arg_child and term.parent_term != ELIDED_TERM:
                # Recs created from term args don't go in the maps.
                # Nor do record term records with elided parent terms
                last_term_map[ELIDED_TERM] = term
                last_term_map[term.record_term] = term

        return root

    @classmethod
    def convert_to_dict(cls, term):
        """Converts a record heirarchy to nested dicts.

        :param term: Root term at which to start conversion

        """

        if term.children:

            d = {}

            for c in term.children:

                if c.child_property_type == 'scalar':
                    d[c.record_term] = cls.convert_to_dict(c)

                elif c.child_property_type == 'sequence':
                    try:
                        d[c.record_term].append(cls.convert_to_dict(c))
                    except (KeyError, AttributeError):
                        # The c.term property doesn't exist, so add a list
                        d[c.record_term] = [cls.convert_to_dict(c)]

                else:
                    try:
                        d[c.record_term].append(cls.convert_to_dict(c))
                    except KeyError:
                        # The c.term property doesn't exist, so add a scalar
                        d[c.record_term] = cls.convert_to_dict(c)
                    except AttributeError as e:
                        # d[c.term] exists, but is a scalar, so convert it to a list

                        d[c.record_term] = [d[c.record_term]] + [cls.convert_to_dict(c)]

            if term.value:
                d[term.term_value_name] = term.value

            return d

        else:
            return term.value

    def errors_as_dict(self):

        errors = []
        for e in self.errors:
            errors.append({
                'file': e.term.file_name,
                'row': e.term.row,
                'col': e.term.col,
                'term': self.join(e.term.parent_term, e.term.record_term),
                'error': str(e)
            })

        return errors

    @staticmethod
    def join(t1, t2):
        return '.'.join((t1, t2))

    def __iter__(self):
        import copy

        last_parent_term = 'root'

        # Remapping the default record value to another property name
        for t in self._term_gen:

            nt = copy.copy(t)

            # Substitute synonyms
            try:
                syn_term = self.synonyms[self.join(t.parent_term, t.record_term)]

                nt.parent_term, nt.record_term = Term.split_term_lower(syn_term);
            except KeyError:
                pass

            if nt.parent_term == ELIDED_TERM and last_parent_term:
                nt.parent_term = last_parent_term
            elif not nt.is_arg_child:
                last_parent_term = nt.record_term

            # Remap integer record terms to names from the parameter map
            try:
                nt.record_term = str(self._param_map[int(t.record_term)])
            except ValueError:
                pass  # the record term wasn't an integer
            except IndexError:
                pass  # Probably no parameter map.

            # Handle other special terms
            if hasattr(self, 'handle_' + t.record_term.lower()):
                getattr(self, 'handle_' + t.record_term.lower())(t)
                if self._remove_special:
                    continue

            nt.child_property_type = self._terms.get(self.join(nt.parent_term, nt.record_term), {}) \
                .get('childpropertytype', 'any')

            nt.term_value_name = self._terms.get(self.join(nt.parent_term, nt.record_term), {}) \
                .get('termvaluename', '@value')

            nt.valid = self.join(nt.parent_term.lower(), nt.record_term.lower()) in self._terms

            yield nt

    def handle_section(self, t):
        self._param_map = [p.lower() if p else i for i, p in enumerate(t.args)]

    def handle_declare(self, t):
        """Load the information in the file referenced by a Delare term, but don't
        insert the terms in the file into the stream"""
        from os.path import dirname, join

        if t.value.startswith('http'):
            fn = t.value.strip('/')
        else:
            fn = join(dirname(t.file_name), t.value.strip('/'))

        ti = TermInterpreter(TermGenerator(CsvPathRowGenerator(fn)), False)

        ti._terms.update({
            NO_TERM + '.section': {'termvaluename': 'name'},
            NO_TERM + '.synonym': {'termvaluename': 'term_name', 'childpropertytype': 'sequence'},
            NO_TERM + '.declareterm': {'termvaluename': 'term_name', 'childpropertytype': 'sequence'},
            NO_TERM + '.declaresection': {'termvaluename': 'section_name', 'childpropertytype': 'sequence'},
            NO_TERM + '.declarevalueset': {'termvaluename': 'name', 'childpropertytype': 'sequence'},
            'declarevalueset.value': {'termvaluename': 'value', 'childpropertytype': 'sequence'},
        })

        try:
            self.import_declare_doc(ti.as_dict())
        except IncludeError as e:
            e.term = t
            self.errors.append(e)

    def import_declare_doc(self, d):
        """Import a declare doc that has been parsed and converted to a dict"""

        if 'declaresection' in d:
            for e in d['declaresection']:
                if e:
                    self._sections[e['section_name'].lower()] = {
                        'args': [v for k, v in sorted((k, v) for k, v in e.items() if isinstance(k, int))],
                        'terms': list()
                    }

        if 'declareterm' in d:
            for e in d['declareterm']:
                terms = self.join(*Term.split_term_lower(e['term_name']))
                self._terms[terms] = e

                if 'section' in e and e['section']:

                    if e['section'] not in self._sections:
                        self._sections[e['section'].lower()] = {
                            'args': [],
                            'terms': list()
                        }

                    st = self._sections[e['section'].lower()]['terms']

                    if e['section'] not in st:
                        st.append(e['term_name'])

        if 'declarevalueset' in d:
            for e in d['declarevalueset']:
                for k, v in self._terms.items():
                    if 'valueset' in v and e.get('name', None) == v['valueset']:
                        v['valueset'] = e['value']


