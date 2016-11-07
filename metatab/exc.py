# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

class ParserError(Exception):
    def __init__(self, *args, **kwargs):
        super(ParserError, self).__init__(*args, **kwargs)
        self.term = kwargs.get('term', None)


class IncludeError(ParserError):
    pass

class GenerateError(ParserError):
    pass