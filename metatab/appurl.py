# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from metatab import DEFAULT_METATAB_FILE
from os.path import basename, join
from rowgenerators import Url
from rowgenerators.appurl.file.file import InnerFile
from rowgenerators.appurl.util import file_ext
from rowgenerators.appurl.web.web import WebUrl

class MetatabUrl(InnerFile, Url):
    match_priority = WebUrl.match_priority - 1

    simple_file_formats = ('csv', 'txt', 'ipynb')

    def __init__(self, url=None, downloader=None, **kwargs):
        kwargs['proto'] = 'metatab'

        u = Url(url, **kwargs)

        assert downloader

        # If there is no file with an extension in the path, assume that this
        # is a filesystem package, and that the path should have DEFAULT_METATAB_FILE
        if file_ext(basename(u.path)) not in ('zip', 'xlsx') + self.simple_file_formats:
            u.path = join(u.path, DEFAULT_METATAB_FILE)

        super().__init__(str(u), downloader=downloader, **kwargs)

        self.scheme_extension = 'metatab'

        if basename(self.path) == DEFAULT_METATAB_FILE:
            frag = ''
        elif self.resource_format in self.simple_file_formats:
            frag = ''
        elif self.resource_format == 'xlsx':
            frag = 'meta'
        elif self.resource_format == 'zip':
            frag = DEFAULT_METATAB_FILE

        self.fragment = [frag, None]

    @classmethod
    def _match(cls, url, **kwargs):
        return url.proto == 'metatab'

    @property
    def resource_format(self):

        resource_format = file_ext(basename(self.path))

        assert resource_format, self.path  # Should have either a definite file, or have added one in __init__

        return resource_format

    @property
    def resource_file(self):

        assert basename(self.resource_url)

        return basename(self.resource_url)

    @property
    def target_file(self):
        if self.path.endswith(DEFAULT_METATAB_FILE):
            return DEFAULT_METATAB_FILE
        elif self.resource_format in self.simple_file_formats:
            return self.resource_file
        elif self.resource_format == 'xlsx':
            return 'meta'
        elif self.resource_format == 'zip':
            return 'metadata.csv'
        else:
            return self.resource_file

    @property
    def target_format(self):
        if self.resource_format in self.simple_file_formats:
            return self.resource_format
        elif self.resource_format == 'xlsx':
            return 'xlsx'
        elif self.resource_format == 'zip':
            return 'csv'
        else:
            return 'csv'

    @property
    def doc(self):
        """Return the metatab document for the URL"""
        from metatab import MetatabDoc
        t = self.get_resource().get_target()
        return MetatabDoc(t.inner)

    @property
    def generator(self):

        from rowgenerators import get_generator

        ##
        ## Hack! This used to be
        ## target = self.get_resource().get_target().inner

        target = self.get_resource().get_target()

        return get_generator(target)

    def get_resource(self):

        if self.scheme == 'file':
            u = self
        else:
            u = WebUrl(str(self), downloader=self._downloader).get_resource()

        return MetatabUrl(str(u), downloader=self._downloader)

    def get_target(self):
        return MetatabUrl(str(self.inner.get_target()), downloader=self._downloader)

    def join_target(self, tf):

        print("Type=", type(self))

        if self.target_file == DEFAULT_METATAB_FILE:
            return self.inner.join_dir(tf)
        else:
            return self.inner.join_target(tf)

    def exists(self):
        return self.inner.exists()
