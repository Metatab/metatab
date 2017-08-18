# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Convert Metatab terms into datapackage.json file
"""

from metatab.exc import ConversionError

type_map = {
    'str': 'string',
    'text': 'string',
    'unicode': 'string',
    'int': 'integer',
    'float': 'number'
}


def convert_to_datapackage(doc):
    dp = doc['root'].as_dict()

    try:
        dp.update(doc['identity'].as_dict())
    except KeyError as e:
        pass

    if not 'name' in dp:
        if 'indentifier' in dp:
            dp['name'] = dp['indentifier']
        else:
            raise ConversionError("Datapackage.json requires a Name or Identity term")

    try:
        table_schemas = {t.value: t.as_dict()['column'] for t in doc['schema']}
    except KeyError as e:
        raise ConversionError("Failed to get schemas: " + str(e))

    file_resources = [fr.arg_props for fr in doc['resources'] if fr.term_is('root.datafile')]

    dp['resources'] = []

    for r in file_resources:

        try:
            columns = table_schemas[r['name']] if r.get('name', '<none>') in table_schemas else table_schemas[
                r['table']]
        except KeyError as e:
            continue

        def mkdict(c):
            d = {}

            for prop in ('name', 'title', 'description'):
                if c.get(prop):
                    d[prop] = c[prop]

            d['type'] = type_map.get(c.get('datatype'), c.get('datatype'))

            return d

        dr = dict(
            path=r['url'],
            name=r['name'],
            schema={'fields': [mkdict(c) for c in columns]}
        )

        dp['resources'].append(dr)

    return dp
