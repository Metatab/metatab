# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""Support for PANDAS dataframes"""

from pandas import DataFrame, Series
import numpy as np
from six import string_types


class MetatabSeries(Series):

    _metadata = ['metatab', 'name'] # Name is defined in the parent

    @property
    def _constructor(self):
        return MetatabSeries

    @property
    def _constructor_expanddim(self):
        return MetatabDataFrame

    @property
    def column(self):
        """Return the infomation about the column"""

        raise NotImplementedError()


class MetatabDataFrame(DataFrame):

    _metadata = [ 'metatab_resource', 'metatab_errors']

    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False, metatab_resource=None):

        self.metatab_resource = metatab_resource
        self.metatab_errors = {}

        super(MetatabDataFrame, self).__init__(data, index, columns, dtype, copy)

    @property
    def _constructor(self):
        return MetatabDataFrame

    @property
    def _constructor_sliced(self):
        return MetatabSeries

    def _getitem_column(self, key):
        c = super(MetatabDataFrame, self)._getitem_column(key)
        c.metatab_resource = self.metatab_resource
        return c

    @property
    def rows(self):
        """Yield rows like a partition does, with a header first, then rows. """

        yield [self.index.name] + list(self.columns)

        for t in self.itertuples():
            yield list(t)


