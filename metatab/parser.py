# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Parser for the Simple Data Package format. The parser consists of several iterable generator
objects.

"""

ROOT_TERM = 'root'  # No parent term -- no '.' --  in term cell
ELIDED_TERM = '<elided_term>'  # A '.' in term cell, but no term before it.


from exc import IncludeError, ParserError
from generate import generateRows


class Term(object):
    """Parses a row into the parts of a term

        Public attributes. These are set externally to the constructor.

        file_name Filename or URL of faile that contains term
        row: Row number of term
        col Column number of term
        term_parent Term was generated from arguments of parent
        child_property_type What datatype to use in dict conversion
        valid Did term pass validation tests? Usually based on DeclaredTerm values.

    """

    def __init__(self, term, value,row=None, col=None, file_name=None, parent = None):
        """

        :param term: Simple or compoint term name
        :param value: Term value, from second column of spreadsheet
        :param term_args: Colums 2+ from term row
        :param term_parent: If set, the term is an arg child, and the term_parent is the parent term.

        """

        def strip_if_str(v):
            try:
                return v.strip()
            except AttributeError:
                return v

        self.parent_term, self.record_term = Term.split_term_lower(term)

        self.value = value

        self.section = None  # Name of section the term is in.

        self.file_name = file_name
        self.row = row
        self.col = col

        # When converting to a dict, what name to to use for the self.value value
        self.term_value_name = '@value'  # May be change in term parsing

        # When converting to a dict, what datatype should be used for this term.
        # Can be forced to list, scalar, dict or other types.
        self.child_property_type = 'any'
        self.valid = None

        self.parent = parent

        self.children = []  # When terms are linked, hold term's children.

        self.is_terminal = self.parent_term == ELIDED_TERM and not self.parent

    @property
    def fqname(self):
        """Fully qualified term name"""

        if self.parent:
            return self.parent.fqname+"."+self.record_term
        else:
            return self.record_term


    @classmethod
    def normalize_term(cls, term):
        return "{}.{}".format(*cls.split_term_lower(term))

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
            parent_term, record_term = ROOT_TERM, term.strip()

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

        from os.path import split

        if self.file_name is not None and self.row is not None:
            parts = split(self.file_name);
            return "{} {}:{} ".format(parts[-1], self.row, self.col)
        elif self.row is not None:
            return " {}:{} ".format(self.row, self.col)
        else:
            return ''

    def add_child(self, child):
        self.children.append(child)

    def join(self):
        return "{}.{}".format(self.parent_term, self.record_term)

    def join_lc(self):
        return "{}.{}".format(self.parent_term.lower(), self.record_term.lower())

    def term_is(self, v):

        if self.record_term.lower() == v.lower() or self.join_lc() == v.lower():
            return True
        else:
            return False

    def __str__(self):
        return "{}{}: {}".format(self.file_ref(), self.fqname, self.value)


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

    def include_path(self, t):
        from os.path import dirname, join

        if not self._path:
            raise IncludeError("Can't include because don't know current path"
                               .format(self._root_directory), term=t)

        include_ref = t.args[0].strip('/')

        if include_ref.startswith('http'):
            path = include_ref
        else:
            path = join(dirname(self._path), include_ref)

    def __iter__(self):
        """An iterator that generates term objects"""

        last_parent = None # Parent for terms with elided parents
        last_term_map = {} # Parents for terms that have specified parents

        t = Term('Root', [], row=0, col=0, file_name=self._path)

        last_term_map[ELIDED_TERM] = t
        last_term_map[t.record_term] = t

        yield t

        for line_n, row in enumerate(self._row_gen, 1):

            if not row[0].strip() or row[0].strip().startswith('#'):
                continue

            t = Term(row[0].lower(),None,
                     row=line_n,col=1,file_name=self._path )

            if not t.is_terminal:
                last_term_map[ELIDED_TERM] = t
                last_term_map[t.record_term] = t

            t.parent = last_term_map[t.parent_term]

            yield t

            for col, value in enumerate([ e for e in (row[1:] if len(row) > 1 else []) if e], 0):
                if str(value).strip():
                    yield Term(t.record_term.lower() + '.' + "arg" + str(col + 1), str(value),
                               row=line_n,
                               col=col + 1,  # The 1st argument starts in col 1
                               file_name=self._path,
                               parent=t)

            if t.term_is('include'):
                try:
                    for t in TermGenerator(generateRows(self.include_path(t))):
                        yield t

                except IncludeError as e:
                    e.term = t
                    raise




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

        self.errors =  set()

        self.root = None
        self.parsed_terms = []

    @property
    def sections(self):
        return self._sections

    @property
    def synonyms(self):

        syns = {}

        for k, v in self._terms.items():
            if 'synonym' in v:
                syns[k.lower()] = v['synonym']

                if not '.' in k:
                    syns[ROOT_TERM+'.'+k.lower()] = v['synonym']

        return syns

    @property
    def terms(self):
        return self._terms

    @property
    def declare_dict(self):

        # Run the parser, if it has not been run yet.
        if not self.root:
            for _ in self: pass

        return {
            'sections': self.sections,
            'terms': self.terms,
        }

    def install_declare_terms(self):
        self._terms.update({
            'root.section': {'termvaluename': 'name'},
            'root.synonym': {'termvaluename': 'term_name', 'childpropertytype': 'sequence'},
            'root.declareterm': {'termvaluename': 'term_name', 'childpropertytype': 'sequence'},
            'root.declaresection': {'termvaluename': 'section_name', 'childpropertytype': 'sequence'},
            'root.declarevalueset': {'termvaluename': 'name', 'childpropertytype': 'sequence'},
            'declarevalueset.value': {'termvaluename': 'value', 'childpropertytype': 'sequence'},
        })

    def run(self):
        """Run the iterator, returning all terms as a list"""

        if not self.root:
            self.parsed_terms = list(self)

        return self

    def as_dict(self):
        """Iterate, link terms and convert to a dict"""

        # Run the parser, if it has not been run yet.
        if not self.root:
            for _ in self: pass

        return self.convert_to_dict(self.root)

    def as_section_dict(self):
        """Iterate, link terms and convert to a dict. LIke as_dict,
         but the top-level of the dict is section names, containing all of the terms
         in that section"""

        # Run the parser, if it has not been run yet.

        d = {}

        if not self.root:
            for _ in self: pass

        for t in self.parsed_terms:
            if t.parent_term == ROOT_TERM:
                section_name = (t.section.value or 'Root').lower()

                if not section_name in d:
                    d[section_name] = []

                d[section_name].append(self.convert_to_dict(t))

        return d

    def substitute_synonym(self, nt):

        if nt.join_lc() in self.synonyms:
            nt.parent_term, nt.record_term = Term.split_term_lower(self.synonyms[nt.join_lc()]);

    @classmethod
    def convert_to_dict(cls, term):
        """Converts a record heirarchy to nested dicts.

        :param term: Root term at which to start conversion

        """

        if not term:
            return None

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
                        # The c.term property doesn't exist, so add a scalar or a msp
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
                'term': e.term.join(),
                'error': str(e)
            })

        return errors

    def __iter__(self):
        import copy

        last_parent_term = 'root'
        last_term_map = {}
        last_section = None
        self.root = None

        try:

            for i, t in enumerate(self._term_gen):

                if t.term_is('root'):
                    last_section = self.root
                    last_term_map[ELIDED_TERM] = self.root
                    last_term_map[self.root.record_term] = self.root

                nt = copy.copy(t)

                if nt.parent_term == ELIDED_TERM:
                    nt.parent_term = last_parent_term

                # Substitute synonyms
                if nt.join_lc() in self.synonyms:
                    nt.parent_term, nt.record_term = Term.split_term_lower(self.synonyms[nt.join_lc()]);

                # Remap integer record terms to names from the parameter map
                try:

                    nt.record_term = str(self._param_map[int(t.record_term)])
                except ValueError:
                    pass  # the record term wasn't an integer

                except IndexError:
                    pass  # Probably no parameter map.

                if nt.term_is('root.section'):
                    self._param_map = [p.lower() if p else i for i, p in enumerate(nt.args)]

                    # Parentage should not persist across sections
                    last_parent_term = self.root.record_term
                    last_section = nt
                    continue

                if nt.term_is('declare'):
                    from os.path import dirname, join

                    if t.value.startswith('http'):
                        fn = nt.value.strip('/')
                    else:
                        fn = join(dirname(nt.file_name), nt.value)

                    nt.value = fn

                    try:
                        ti = TermInterpreter(TermGenerator(generateRows(fn)), False)
                        ti.install_declare_terms()
                        self.import_declare_doc(ti.as_dict())

                    except IncludeError as e:
                        e.term = t
                        self.errors.add(e)
                        raise

                if nt.term_is('header'):
                    default_child_property_type = nt.value

                    continue

                nt.child_property_type = self._terms.get(nt.join(), {}).get('childpropertytype', 'any')

                nt.term_value_name = self._terms.get(nt.join(), {}).get('termvaluename', '@value')

                nt.valid = nt.join_lc() in self._terms

                nt.section = last_section;

                if not nt.is_terminal:
                    last_parent_term = nt.record_term
                    # Recs created from term args don't go in the maps.
                    # Nor do record term records with elided parent terms
                    last_term_map[ELIDED_TERM] = nt
                    last_term_map[nt.record_term] = nt

                try:
                    if nt.is_terminal:
                        parent = last_term_map[last_parent_term]
                    else:
                        parent = last_term_map[nt.parent_term]

                    parent.add_child(nt)
                except KeyError as e:
                    import json
                    raise ParserError(("Failed to find parent term in last term map: {} {} \n"+
                                      "Term: \n    {}\nParents:\n    {}\nSynonyms:\n{}")
                                          .format(e.__class__.__name__, e, nt,
                                                  last_term_map.keys(),
                                                  json.dumps(self.synonyms, indent = 4)))

                self.parsed_terms.append(nt)

                yield nt

        except IncludeError as e:
            self.errors.add(e)
            raise

    def import_declare_doc(self, d):
        """Import a declare doc that has been parsed and converted to a dict"""

        if 'declaresection' in d:
            for e in d['declaresection']:
                if e:
                    self._sections[e['section_name'].lower()] = {
                        'args': [v for k, v in sorted((k, v) for k, v in e.items() if isinstance(k, int))],
                        'terms': []
                    }

        if 'declareterm' in d:
            for e in d['declareterm']:

                if not isinstance(e, dict):  # It could be a string in odd cases
                    continue

                self._terms[Term.normalize_term(e['term_name'])] = e

                if 'section' in e and e['section']:

                    if e['section'] not in self._sections:
                        self._sections[e['section'].lower()] = {
                            'args': [],
                            'terms': []
                        }

                    st = self._sections[e['section'].lower()]['terms']

                    if e['section'] not in st:
                        st.append(e['term_name'])

        if 'declarevalueset' in d:
            for e in d['declarevalueset']:
                for k, v in self._terms.items():
                    if 'valueset' in v and e.get('name', None) == v['valueset']:
                        v['valueset'] = e['value']


