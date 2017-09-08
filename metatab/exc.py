# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""


class MetatabError(Exception):
    pass




class ReferenceError(MetatabError):
    pass


class ParserError(MetatabError):
    def __init__(self, *args, **kwargs):
        super(ParserError, self).__init__(*args, **kwargs)
        self.term = kwargs.get('term', None)


class IncludeError(MetatabError):
    def __init__(self, *args, **kwargs):
        self.message = ''
        super(IncludeError, self).__init__(*args, **kwargs)


class DeclarationError(ParserError):
    pass


class GenerateError(MetatabError):
    pass


class ConversionError(MetatabError):
    pass

