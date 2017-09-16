# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""


from metapack.exc import MetapackError, ResourceError
from appurl.util import parse_url_to_dict, unparse_url_dict, file_ext
from os.path import basename, join, dirname
from appurl import Url, parse_app_url, DownloadError
from appurl.web import WebUrl
from appurl.file import FileUrl

from metatab import DEFAULT_METATAB_FILE


class _MetapackUrl(object):


    def exists(self):

        if self.inner.proto == 'file':
            return self.inner.exists()
        else:
            # Hack, really ought to implement exeists() for web urls.
            return True


class MetapackDocumentUrl(Url, _MetapackUrl):
    def __init__(self, url=None, downloader=None, **kwargs):
        kwargs['proto'] = 'metapack'

        u = Url(url, **kwargs)

        assert downloader

        # If there is no file with an extension in the path, assume that this
        # is a filesystem package, and that the path should have DEFAULT_METATAB_FILE
        if file_ext(basename(u.path)) not in ('zip', 'xlsx', 'csv'):
            u.path = join(u.path, DEFAULT_METATAB_FILE)

        super().__init__(str(u), downloader=downloader, **kwargs)

        self.scheme_extension = 'metapack'

        if basename(self.path) == DEFAULT_METATAB_FILE:
            frag = ''
        elif self.resource_format == 'csv':
            frag = ''
        elif self.resource_format == 'xlsx':
            frag = 'meta'
        elif self.resource_format == 'zip':
            frag = DEFAULT_METATAB_FILE

        self.fragment = [frag,None]



    @classmethod
    def match(cls, url, **kwargs):
        raise MetapackError("This class should not be contructed through matching")


    @property
    def resource_format(self):

        resource_format = file_ext(basename(self.path))

        assert resource_format, self.path # Should have either a definite file, or have added one in __init__

        return resource_format

    @property
    def resource_file(self):

        assert basename(self.resource_url)

        return basename(self.resource_url)

    @property
    def target_file(self):
        if self.path.endswith(DEFAULT_METATAB_FILE):
            return DEFAULT_METATAB_FILE
        elif self.resource_format == 'csv':
            return self.resource_file
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
        return MetapackDoc(self.get_resource().get_target(), package_url=self.package_url)

    @property
    def generator(self):

        from rowgenerators import get_generator

        t = self.get_resource().get_target().inner

        return get_generator(t)

    def resolve_url(self, resource_name):
        """Return a URL to a local copy of a resource, suitable for get_generator()"""

        if self.target_format == 'csv' and self.target_file != DEFAULT_METATAB_FILE:
            # For CSV packages, need to get the package and open it to get the resoruce URL, becuase
            # they are always absolute web URLs and may not be related to the location of the metadata.
            s = self.get_resource()
            rs = s.doc.resource(resource_name)
            return parse_app_url(rs.url)
        else:
            jt = self.join_target(resource_name)
            rs = jt.get_resource()
            t = rs.get_target()
        return t


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
            return MetapackPackageUrl(str(u.clear_fragment()), downloader=self._downloader)
        else:
            return MetapackPackageUrl(str(self.clear_fragment()), downloader=self._downloader)

    def get_resource(self):

        if self.scheme == 'file':
            return self
        else:

            u = WebUrl(str(self), downloader=self._downloader)
            r = u.get_resource()
            return MetapackDocumentUrl(str(r), downloader=self._downloader)

    def get_target(self):
        return self.inner.get_target()

    def join_target(self, tf):
        if self.target_file == DEFAULT_METATAB_FILE:
            return self.inner.join_dir(tf)
        else:
            return self.inner.join_target(tf)


class MetapackPackageUrl(FileUrl, _MetapackUrl):
    """Special version of MetapackUrl for package urls, which never have a fragment"""

    def __init__(self, url=None, downloader=None, **kwargs):
        kwargs['proto'] = 'metapack'

        super().__init__(url, downloader=downloader, **kwargs)
        self.scheme_extension = 'metapack'

        self.fragment = None
        self.query = None

        assert self._downloader

    @property
    def package_url(self):
        return self

    @property
    def metadata_url(self):

        return MetapackDocumentUrl(str(self.clone().clear_fragment()), downloader=self._downloader).metadata_url


    def rebuild_fragment(self):
        self.fragment = ''

    def join_resource_name(self,v):
        """Return a MetapackResourceUrl that includes a reference to the resource. Returns a
        MetapackResourceUrl, which will have a a fragment """
        d = self.dict
        d['fragment'] = [v,None]
        return MetapackResourceUrl(downloader=self._downloader, **d )

    def join_resource_path(self, v):
        """Return a regular AppUrl that combines the package with a URL path """
        return self.inner.join(v)


    def join_target(self, tf):
        """Like join(), but returns the inner URL, not a package url class"""
        if self.target_file == DEFAULT_METATAB_FILE:
            return self.inner.join_dir(tf)
        else:
            return self.inner.join_target(tf)

    def resolve_url(self, resource_name):
        """Return a URL to a local copy of a resource, suitable for get_generator()

        For Package URLS, resolution involves generating a URL to a data file from the package URL and the
        value of a resource. The resource value, the url, can be one of:

        - An absolute URL, with a web scheme
        - A relative URL, relative to the package, with a file scheme.

        URLs with non-file schemes are returned. File scheme are assumed to be relative to the package,
        and are resolved according to the type of resource.

        """

        u = parse_app_url(resource_name)

        if u.scheme != 'file':
            t = u

        elif self.target_format == 'csv' and self.target_file != DEFAULT_METATAB_FILE:
            # Thre are two forms for CSV package URLS:
            # - A CSV package, which can only have absolute URLs
            # - A Filesystem package, which can have relative URLs.

            # The complication is that the filsystem package usually has a metadata file named
            # DEFAULT_METATAB_FILE, which can distinguish it from a CSV package, but it's also possible
            # to have a filesystem package with a non standard package name.

            # So, this clause can happed for two cases: A CSV package or a Filesystem package with a nonstandard
            # metadata file name.

            # For CSV packages, need to get the package and open it to get the resource URL, because
            # they are always absolute web URLs and may not be related to the location of the metadata.
            s = self.get_resource()
            rs = s.metadata_url.doc.resource(resource_name)
            if rs is not None:
                t = parse_app_url(rs.url)
            else:
                raise ResourceError("No resource for '{}' in '{}' ".format(resource_name, self))


        else:
            jt = self.join_target(resource_name)
            try:
                rs = jt.get_resource()
            except DownloadError:
                raise ResourceError(
                    "Failed to download resource for '{}' for '{}' in '{}'".format(jt, resource_name, self))
            t = rs.get_target()

        return t

    @property
    def inner(self):
        return super().inner


class MetapackResourceUrl(FileUrl, _MetapackUrl):
    def __init__(self, url=None, downloader=None, **kwargs):
        kwargs['proto'] = 'metapack'

        super().__init__(url, downloader=downloader, **kwargs)
        self.scheme_extension = 'metapack'

        # Expand the path in the same was as the document URL

        # Using .clone() causes recursion
        d = self.dict
        d['fragment'] = None

        md = MetapackDocumentUrl(None,downloader = downloader, **d)
        self.path = md.path

    @classmethod
    def match(cls, url, **kwargs):
        raise MetapackError("This class should not be contructed through matching")


    @property
    def target_file(self):
        from urllib.parse import unquote_plus

        if self.fragment[0]:
            return self.fragment[0]

        return None


    @property
    def doc(self):
        """Return the metatab document for the URL"""
        return self.metadata_url.doc

    @property
    def metadata_url(self):
        assert self._downloader
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
            mru = MetapackResourceUrl(str(r), downloader=self._downloader)
            return mru

    def get_target(self):

        return self.resource
        #return self.resolve_url(self.target_file)
        #r = self.get_resource()
        #pu = self.package_url
        #resolved = pu.resolve_url(self.target_file)
        #return resolved
        #return self.inner.get_target()

    @property
    def generator(self):
        # Use fragment b/c it could be target_file, for .zip, or target_segment, for .xlsx
        return self.resource

    @property
    def resource(self):

        doc = self.metadata_url.doc
        r =  doc.resource(self.target_file)
        return r


# Would have made this a function, but it needs to be a class to have the match() method
class MetapackUrl(Url):
    """Implements __new__ to return either a  MetapackResourceUrl or a MetapackDocumentUrl"""

    match_priority = 18

    def __new__(cls, url=None, downloader=None, **kwargs):

        assert downloader

        u = Url(url, **kwargs)

        if u.fragment[0]:
            return MetapackResourceUrl(url, downloader, **kwargs)
        else:
            return MetapackDocumentUrl(url, downloader, **kwargs)

    @classmethod
    def match(cls, url, **kwargs):
        """Return True if this handler can handle the input URL"""
        return url.proto in ('metapack', 'metatab')

class JupyterNotebookUrl(FileUrl):
    """IPYthon Notebook URL"""

    def __init__(self, url=None, **kwargs):
        kwargs['proto'] = 'ipynb'
        super().__init__(url, **kwargs)

    @classmethod
    def match(cls, url, **kwargs):
        return url.resource_format == 'ipynb'

    def get_target(self, mode=None):
        return self



