# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE.txt

""" """

from rowgenerators.source import Source

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

