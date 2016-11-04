

class ParserError(Exception):
    def __init__(self, *args, **kwargs):
        super(ParserError, self).__init__(*args, **kwargs)
        self.term = kwargs.get('term', None)


class IncludeError(ParserError):
    pass

class GenerateError(ParserError):
    pass