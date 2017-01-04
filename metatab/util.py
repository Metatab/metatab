# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Classes to build a Metatab document
"""



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