# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from metapack.exc import MetapackError
from appurl.util import parse_url_to_dict, unparse_url_dict, file_ext
from os.path import basename, join, dirname
from appurl import Url
from appurl.web import WebUrl
from appurl.file import FileUrl

from metatab import DEFAULT_METATAB_FILE


class _MetapackUrl(object):


    def exists(self):

        return self.inner.exists()



class MetapackDocumentUrl(Url, _MetapackUrl):
    def __init__(self, url=None, downloader=None, **kwargs):
        kwargs['proto'] = 'metapack'

        super().__init__(url, downloader=downloader, **kwargs)

        self.scheme_extension = 'metapack'

    @classmethod
    def match(cls, url, **kwargs):
        raise MetapackError("This class should not be contructed through matching")


    @property
    def resource_format(self):

        resource_format = file_ext(basename(self.path))

        if resource_format not in ('zip', 'xlsx', 'csv'):
            resource_format = 'csv'

        return resource_format

    @property
    def resource_file(self):

        if not basename(self.resource_url):
            return DEFAULT_METATAB_FILE
        else:
            return basename(self.resource_url)


    @property
    def target_file(self):
        if self.resource_format == 'csv':
            return DEFAULT_METATAB_FILE
        elif self.resource_format == 'xlsx':
            return 'meta'
        elif self.resource_format == 'zip':
            return 'metadata.csv'
        else:
            return self.resource_file

    @property
    def target_format(self):
        if self.resource_format == 'csv':
            return 'csv'
        elif self.resource_format == 'xlsx':
            return 'xlsx'
        elif self.resource_format == 'zip':
            return 'csv'
        else:
            return 'csv'

    @property
    def doc(self):
        """Return the metatab document for the URL"""
        from metapack import MetapackDoc
        return MetapackDoc(self)

    @property
    def generator(self):

        from rowgenerators import get_generator

        t = self.get_resource().get_target().inner

        return get_generator(t)

    @property
    def metadata_url(self):

        if not basename(self.resource_url):
            return self.clone(path=join(self.path,DEFAULT_METATAB_FILE))
        else:
            return self.clone()

    @property
    def package_url(self):
        """Return the package URL associated with this metadata"""
        if self.resource_file == DEFAULT_METATAB_FILE:
            u = self.inner.clone().clear_fragment()
            u.path = dirname(self.path) + '/'
            u.scheme_extension = 'metapack'
            return u
        else:
            return self.inner.clear_fragment()

    def get_resource(self):

        if self.scheme == 'file':
            return self
        else:
            u = WebUrl(str(self), downloader=self._downloader)
            r = u.get_resource()
            return MetapackDocumentUrl(str(r), downloader=self._downloader)

    def get_target(self):
        return self.inner.get_target().clear_fragment()

class MetapackResourceUrl(FileUrl, _MetapackUrl):
    def __init__(self, url=None, downloader=None, **kwargs):
        kwargs['proto'] = 'metapack'

        super().__init__(url, downloader=downloader, **kwargs)
        self.scheme_extension = 'metapack'

        # Expand the path in the same was as the document URL

        # Using .clone() causes recursion
        d = self.dict
        d['fragment'] = None

        md = MetapackDocumentUrl(None, **d)
        self.path = md.path

    @classmethod
    def match(cls, url, **kwargs):
        raise MetapackError("This class should not be contructed through matching")


    @property
    def target_file(self):
        from urllib.parse import unquote_plus

        if self.fragment:

            frag_parts = unquote_plus(self.fragment).split(';')

            if frag_parts:
                return frag_parts[0]

        return None


    @property
    def doc(self):
        """Return the metatab document for the URL"""
        return self.metadata_url.doc

    @property
    def metadata_url(self):
        return MetapackDocumentUrl(str(self.clone().clear_fragment()), downloader=self._downloader).metadata_url

    @property
    def package_url(self):
        """Return the package URL associated with this metadata"""
        return MetapackDocumentUrl(str(self.clear_fragment()), downloader=self._downloader).package_url

    def get_resource(self):
        if self.scheme == 'file':
            return self
        else:
            u = WebUrl(str(self), downloader=self._downloader)
            r = u.get_resource()
            return MetapackResourceUrl(str(r), downloader=self._downloader)

    def get_target(self):
        m = self.metadata_url

        return m

    @property
    def generator(self):
        # Use fragment b/c it could be target_file, for .zip, or target_segment, for .xlsx
        return self.resource

    @property
    def resource(self):
        return self.metadata_url.doc.resource(self.fragment)


# Would have made this a function, but it needs to be a class to have the match() method
class MetapackUrl(Url):
    """Implements __new__ to return either a  MetapackResourceUrl or a MetapackDocumentUrl"""

    match_priority = 18

    def __new__(cls, url=None, downloader=None, **kwargs):

        u = Url(url, **kwargs)

        if u.fragment:
            return MetapackResourceUrl(url, downloader, **kwargs)
        else:
            return MetapackDocumentUrl(url, downloader, **kwargs)

    @classmethod
    def match(cls, url, **kwargs):
        """Return True if this handler can handle the input URL"""
        return url.proto in ('metapack', 'metatab') and url.scheme in ('http', 'https')


class JupyterUrl(FileUrl):
    pass
