# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Generate rows from a variety of paths, references or other input
"""

from .exc import IncludeError, GenerateError

class WebResolver(object):

    def fetch_row_source(self, url):
        pass

    def find_decl_doc(self, name):


        raise IncludeError(name)

        import requests
        from requests.exceptions import InvalidSchema
        url = METATAB_ASSETS_URL + name + '.csv'
        try:
            # See if it exists online in the official repo
            r = requests.head(url, allow_redirects=False)
            if r.status_code == requests.codes.ok:
                return url

        except InvalidSchema:
            pass  # It's probably FTP


    def get_row_generator(self, ref, cache=None):

        """Return a row generator for a reference"""
        from inspect import isgenerator
        from rowgenerators import get_generator

        g = get_generator(ref)

        if not g:
            raise GenerateError("Cant figure out how to generate rows from {} ref: {}".format(type(ref), ref))
        else:
            return g

