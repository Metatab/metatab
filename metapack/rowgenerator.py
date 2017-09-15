# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

from rowgenerators import Source


class JupyterNotebookSource(Source):
    """Generate rows from an IPython Notebook.

     This generator will execute a Jupyter notebook. Before execution, it adds an "%mt_materalize"
     magic to the notebook, which will cause the target dataframe to be written to a temporary file, and
     the temporary file is yielded to the caller. Not most efficient, but it fits the model.
     """

    def __init__(self, ref, cache=None, working_dir=None, **kwargs):
        super().__init__(ref, cache, working_dir, **kwargs)

    def start(self):
        pass

    def finish(self):
        pass


    def __iter__(self):

        import pandas as pd
        from metapack.jupyter.exec import execute_notebook
        from tempfile import mkdtemp
        from os import remove, makedirs
        from os.path import join, isdir
        from csv import reader
        from shutil import rmtree

        dr_name = None

        try:
            self.start()

            dr_name = mkdtemp()

            if not isdir(dr_name):
                makedirs(dr_name)

            # The execute_motebook() function will add a cell with the '%mt_materialize' magic,
            # with a path that will case the file to be written to the same location as
            # path, below.
            nb = execute_notebook(self.ref.path, dr_name, [self.ref.target_file], True)

            path = join(dr_name, self.ref.target_file + ".csv")

            with open(path) as f:
                yield from reader(f)

            self.finish()

        finally:

            if dr_name:
                try:
                    rmtree(dr_name)
                except FileNotFoundError:
                    pass


class PandasDataframeSource(Source):
    """Iterates a pandas dataframe  """


    def __init__(self, url, df, cache, working_dir=None, **kwargs):
        super().__init__(url, cache, working_dir, **kwargs)

        self._df = df

    def __iter__(self):

        self.start()

        df = self._df

        if len(df.index.names) == 1 and df.index.names[0] == None:
            # For an unnamed, single index, assume that it is just a row number
            # and we don't really need it

            yield list(df.columns)

            for index, row in df.iterrows():
                yield list(row)

        else:

            # Otherwise, either there are more than

            index_names = [n if n else "index{}".format(i) for i,n in enumerate(df.index.names)]

            yield index_names + list(df.columns)

            if len(df.index.names) == 1:
                idx_list = lambda x: [x]
            else:
                idx_list = lambda x: list(x)

            for index, row in df.iterrows():
                yield idx_list(index) + list(row)


        self.finish()





