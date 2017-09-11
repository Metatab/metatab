


class NotebootUrl(Url):
    """IPYthon Notebook URL"""

    def __init__(self, url, **kwargs):
        kwargs['proto'] = 'ipynb'

        super(NotebootUrl, self).__init__(url, **kwargs)

    @classmethod
    def match(cls, url, **kwargs):
        return extract_proto(url) == 'ipynb'

    def _extract_parts(self, url, kwargs):
        parts = self.url_parts(url, **kwargs)

        self.url = reparse_url(url, assume_localhost=True,
                               scheme=parts.scheme if parts.scheme != 'ipynb' else 'file',
                               scheme_extension='ipynb')

        self.parts = self.url_parts(self.url, **kwargs)

    @property
    def path(self):
        return self.parts.path

    def _process_resource_url(self):
        self.resource_url = unparse_url_dict(self.parts.__dict__,
                                             scheme=self.parts.scheme if self.parts.scheme != 'ipynb' else 'file',
                                             scheme_extension=False,
                                             fragment=False).strip('/')

        self.resource_file = basename(self.resource_url)

        if not self.resource_format:
            self.resource_format = file_ext(self.resource_file)

    def _process_fragment(self):
        self.target_segment = self.parts.fragment

    def _process_target_file(self):
        super(NotebootUrl, self)._process_target_file()

        assert self.target_format == 'ipynb', self.target_format

