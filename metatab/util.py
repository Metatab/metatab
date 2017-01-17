# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Classes to build a Metatab document
"""

def declaration_path(name):
    """Return the path to an included declaration"""
    from os.path import dirname, join, exists
    import metatab.declarations
    from metatab.exc import IncludeError

    d = dirname(metatab.declarations.__file__)

    path = join(d,name)

    if not exists(path):
        path = join(d, name + '.csv')

    if not exists(path):
        raise IncludeError("No local declaration file for name '{}' ".format(name))

    return path


# From http://stackoverflow.com/a/295466
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.type(
    """
    import re
    import unicodedata
    from six import text_type
    value = text_type(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf8')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value


def flatten(d, sep='.'):
    """Flatten a data structure into tuples"""
    def _flatten(e, parent_key='', sep='.'):
        import collections

        prefix = parent_key+sep if parent_key else ''

        if isinstance(e, collections.MutableMapping):
            return tuple( (prefix+k2, v2) for k, v in e.items() for k2,v2 in _flatten(v,  k, sep ) )
        elif isinstance(e, collections.MutableSequence):
            return tuple( (prefix+k2, v2) for i, v in enumerate(e) for k2,v2 in _flatten(v,  str(i), sep ) )
        else:
            return (parent_key, (e,)),

    return tuple( (k, v[0]) for k, v in _flatten(d, '', sep) )