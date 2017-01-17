# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Convert Metatab terms into datapackage.json file
"""


type_map = {

}

def convert_to_datapackage(doc):

    dp = doc['root'].as_dict()

    table_schemas = {t.value: t.as_dict()['column'] for t in doc['schema']}
    file_resources = [fr.properties for fr in doc['resources'] if fr.term_is('root.datafile')]

    for r in file_resources:

        try:
            columns = table_schemas[r['name']]
        except KeyError:
            continue

        dr = dict(
            path=r['url'],
            name=r['name'],
            schema=[
                dict(
                    name=c.get('name'),
                    title=c.get('title'),
                    type=type_map.get(c.get('datatype')),
                    description=c.get('description')
                ) for c_name, c in columns
            ]

        )

    return dp


