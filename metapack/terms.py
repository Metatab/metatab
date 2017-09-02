from itertools import islice

from appurl import parse_app_url
from metapack import MetapackError
from metapack.doc import EMPTY_SOURCE_HEADER
from metapack.exc import PackageError
from metatab import Term
from rowgenerators import DownloadError, get_generator
from rowpipe import RowProcessor

class Resource(Term):

        # These property names should return null if they aren't actually set.
        _common_properties = 'url name description schema'.split()

        def __init__(self, term, value, term_args=False, row=None, col=None, file_name=None, file_type=None,
                     parent=None, doc=None, section=None,
                     ):

            #self.base_url = base_url
            #self.package = package
            #self.code_path = code_path
            #self.env = env if env is not None else {}

            self.errors = {}  # Typecasting errors

            super().__init__(term, value, term_args, row, col, file_name, file_type, parent, doc, section)


        @property
        def base_url(self):
            """Base URL for resolving resource URLs"""

            return self.doc.package_url if self.doc.package_url else self.doc._ref

        @property
        def env(self):
            """The execution context for rowprocessors and row-generating notebooks and functions. """

            return self.doc.env



        @property
        def code_path(self):
            from .util import slugify
            from fs.errors import DirectoryExists

            sub_dir = 'resource-code/{}'.format(slugify(self.doc.name))
            try:
                self.doc.cache.makedirs(sub_dir)
            except DirectoryExists:
                pass

            return self.doc.cache.opendir(sub_dir).getsyspath(slugify(self.name)+'.py')

        @property
        def _self_url(self):
            """Return the URl value, which might just be the value, and not self.url, if the document
            declartion is broken"""
            try:
                if self.url:
                    return self.url
            finally:  # WTF? No idea, probably wrong.
                return self.value


        @property
        def resolved_url(self):
            """Return a URL that properly combines the base_url and a possibly relative
            resource url"""


            if self.base_url:
                u = parse_app_url(self.base_url)

            else:
                u = parse_app_url(self.doc.package_url)

            if not self._self_url:
                return None

            nu = u.component_url(self._self_url)

            # The manipulations of component_url can result in the .inner sub-url being very different from the
            # .resource_url sub-url. Reparsing should fix all of that.
            return parse_app_url(str(nu))

        def _name_for_col_term(self, c, i):

            altname = c.get_value('altname')
            name = c.value if c.value != EMPTY_SOURCE_HEADER else None
            default = "col{}".format(i)

            for n in [altname, name, default]:
                if n:
                    return n

        @property
        def schema_name(self):
            """The value of the Name or Schema property"""
            return self.get_value('schema', self.get_value('name'))

        @property
        def schema_table(self):
            """Deprecated. Use schema_term()"""
            return self.schema_term

        @property
        def schema_term(self):
            """Return the Table term for this resource, which is referenced either by the `table` property or the
            `schema` property"""

            if not self.name:
                raise MetapackError("Resource for url '{}' doe not have name".format(self.url))

            t = self.doc.find_first('Root.Table', value=self.get_value('name'))
            frm = 'name'

            if not t:
                t = self.doc.find_first('Root.Table', value=self.get_value('schema'))
                frm = 'schema'

            if not t:
                frm = None

            return t

        @property
        def headers(self):
            """Return the headers for the resource. Returns the AltName, if specified; if not, then the
            Name, and if that is empty, a name based on the column position. These headers
            are specifically applicable to the output table, and may not apply to the resource source. FOr those headers,
            use source_headers"""

            t = self.schema_term

            if t:
                return [self._name_for_col_term(c, i)
                        for i, c in enumerate(t.children, 1) if c.term_is("Table.Column")]
            else:
                return None

        @property
        def source_headers(self):
            """"Returns the headers for the resource source. Specifically, does not include any header that is
            the EMPTY_SOURCE_HEADER value of _NONE_"""

            t  = self.schema_term

            if t:
                return [self._name_for_col_term(c, i)
                        for i, c in enumerate(t.children, 1) if c.term_is("Table.Column")
                        and c.get_value('name') != EMPTY_SOURCE_HEADER
                        ]
            else:
                return None

        def columns(self):

            t  = self.schema_term

            if not t:
                return

            for i, c in enumerate(t.children):

                if c.term_is("Table.Column"):

                    # This code originally used c.properties,
                    # but that fails for the line oriented form, where the
                    # sections don't have args, so there are no properties.
                    p = {}

                    for cc in c.children:
                        p[cc.record_term_lc] = cc.value

                    p['name'] = c.value

                    p['header'] = self._name_for_col_term(c, i)
                    yield p

        def row_processor_table(self):
            """Create a row processor from the schema, to convert the text velus from the
            CSV into real types"""
            from rowpipe.table import Table

            type_map = {
                None: None,
                'string': 'str',
                'text': 'str',
                'number': 'float',
                'integer': 'int'
            }

            def map_type(v):
                return type_map.get(v, v)

            doc = self.doc

            table_term = doc.find_first('Root.Table', value=self.get_value('name'))

            if not table_term:
                table_term = doc.find_first('Root.Table', value=self.get_value('schema'))

            if table_term:

                t = Table(self.get_value('name'))

                col_n = 0

                for c in table_term.children:
                    if c.term_is('Table.Column'):
                        t.add_column(self._name_for_col_term(c, col_n),
                                     datatype=map_type(c.get_value('datatype')),
                                     valuetype=map_type(c.get_value('valuetype')),
                                     transform=c.get_value('transform')
                                     )
                        col_n += 1

                return t

            else:
                return None

        @property
        def row_generator(self):

            d = self.all_props

            d['source'] = self.resolved_url.get_resource().get_target()
            d['target_format'] = d.get('format')
            d['target_segment'] = d.get('segment')
            d['target_file'] = d.get('file')
            d['encoding'] = d.get('encoding', 'utf8')

            generator_args = dict(d.items())
            # For ProgramSource generator, These become values in a JSON encoded dict in the PROPERTIE env var
            generator_args['working_dir'] = self._doc.doc_dir
            generator_args['metatab_doc'] = self._doc.ref
            generator_args['metatab_package'] = str(self._doc.package_url)

            # These become their own env vars.
            generator_args['METATAB_DOC'] = self._doc.ref
            generator_args['METATAB_WORKING_DIR'] = self._doc.doc_dir
            generator_args['METATAB_PACKAGE'] = str(self._doc.package_url)

            d['cache'] = self._doc._cache
            d['working_dir'] = self._doc.doc_dir
            d['generator_args'] = generator_args

            g = get_generator(**d)

            return g

        def _get_header(self):
            """Get the header from the deinfed header rows, for use  on references or resources where the schema
            has not been run"""

            try:
                header_lines = [int(e) for e in str(self.get_value('headerlines', 0)).split(',')]
            except ValueError as e:
                header_lines = [0]

            # We're processing the raw datafile, with no schema.
            header_rows = islice(self.row_generator, min(header_lines), max(header_lines) + 1)

            from tableintuit import RowIntuiter
            headers = RowIntuiter.coalesce_headers(header_rows)

            return headers

        def __iter__(self):
            """Iterate over the resource's rows"""

            headers = self.headers

            # There are several args for SelectiveRowGenerator, but only
            # start is really important.
            try:
                start = int(self.get_value('startline', 1))
            except ValueError as e:
                start = 1

            if headers:  # There are headers, so use them, and create a RowProcess to set data types
                yield headers

                rg = RowProcessor(islice(self.row_generator, start, None),
                                  self.row_processor_table(),
                                  source_headers=self.source_headers,
                                  env=self.env,
                                  code_path=self.code_path)

            else:
                headers = self._get_header()  # Try to get the headers from defined header lines

                yield headers
                rg = islice(self.row_generator, start, None)

            yield from rg

            try:
                self.errors = rg.errors if rg.errors else {}
            except AttributeError:
                self.errors = {}

        @property
        def iterdict(self):
            """Iterate over the resource in dict records"""

            headers = None

            for row in self:

                if headers is None:
                    headers = row
                    continue

                yield dict(zip(headers, row))

        def _convert_geometry(self, df):

            if 'geometry' in df.columns:

                try:
                    import geopandas as gpd
                    shapes = [row['geometry'].shape for i, row in df.iterrows()]
                    df['geometry'] = gpd.GeoSeries(shapes)
                except ImportError:
                    raise
                    pass

        def _upstream_dataframe(self, limit=None):


            return None

            rg = self.row_generator

            # Maybe generator has it's own Dataframe method()
            try:
                return rg.generator.dataframe()
            except AttributeError:
                pass

            # If the source is another package, use that package's dataframe()
            if isinstance(rg.generator, MetapackSource):
                try:
                    return rg.generator.resource.dataframe(limit=limit)
                except AttributeError:
                    if rg.generator.package is None:
                        raise PackageError(
                            "Failed to get reference package for {}".format(rg.generator.spec.resource_url))
                    if rg.generator.resource is None:
                        raise PackageError(
                            "Failed to get reference resource for '{}' ".format(rg.generator.spec.target_segment))
                    else:
                        raise

            return None

        def dataframe(self, limit=None):
            """Return a pandas datafrome from the resource"""

            from metapack.jupyter.pandas import MetatabDataFrame

            df = self._upstream_dataframe(limit)

            if df is not None:
                return df

            rg = self.row_generator

            # Just normal data, so use the iterator in this object.
            headers = next(islice(self, 0, 1))
            data = islice(self, 1, None)

            df = MetatabDataFrame(list(data), columns=headers, metatab_resource=self)

            self.errors = df.metatab_errors = rg.errors if hasattr(rg, 'errors') and rg.errors else {}

            return df

        @property
        def sub_package(self):
            """For references to Metapack resoruces, the original package"""


            rg = self.row_generator

            if isinstance(rg.generator, MetapackSource):
                return rg.generator.package
            else:
                return None

        @property
        def sub_resource(self):
            """For references to Metapack resoruces, the original package"""


            rg = self.row_generator

            if isinstance(rg.generator, MetapackSource):
                return rg.generator.resource
            else:
                return None

        def _repr_html_(self):

            try:
                return self.sub_resource._repr_html_()
            except AttributeError:
                pass
            except DownloadError:
                pass

            return (
                   "<h3><a name=\"resource-{name}\"></a>{name}</h3><p><a target=\"_blank\" href=\"{url}\">{url}</a></p>" \
                   .format(name=self.name, url=self.resolved_url)) + \
                   "<table>\n" + \
                   "<tr><th>Header</th><th>Type</th><th>Description</th></tr>" + \
                   '\n'.join(
                       "<tr><td>{}</td><td>{}</td><td>{}</td></tr> ".format(c.get('header', ''),
                                                                            c.get('datatype', ''),
                                                                            c.get('description', ''))
                       for c in self.columns()) + \
                   '</table>'

        @property
        def markdown(self):

            from .html import ckan_resource_markdown
            return ckan_resource_markdown(self)


class Reference(Resource):


    def dataframe(self, limit=None):
        """Return a Pandas Dataframe using read_csv or read_excel"""

        from pandas import read_csv
        from rowgenerators import download_and_cache
        from metapack.jupyter.pands import MetatabDataFrame, MetatabSeries

        df = self._upstream_dataframe(limit)

        if df is not None:
            self._convert_geometry(df)
            return df

        rg = self.row_generator

        # Download, cache and possibly extract an inner file.
        info = download_and_cache(rg.generator.spec, self._doc._cache, logger=None, working_dir='', callback=None)

        try:
            skip = int(self.get_value('startline', 1)) - 1
        except ValueError as e:
            skip = 0

        df = read_csv(
            info['sys_path'],
            skiprows=skip
        )

        df.columns = self._get_header()

        df.__class__ = MetatabDataFrame
        df.metatab_resource = self
        df.metatab_errors = {}

        for c in df.columns:
            df[c].__class__ = MetatabSeries


        return df

class Distribution(Term):

    def distributions(self, type=False):
        """"Return a dict of distributions, or if type is specified, just the first of that type

        """
        from collections import namedtuple

        Dist = namedtuple('Dist', 'type url term')

        def dist_type(url):

            if url.target_file == 'metadata.csv':
                return 'fs'
            elif url.target_format == 'xlsx':
                return 'excel'
            elif url.resource_format == 'zip':
                return "zip"
            elif url.target_format == 'csv':
                return "csv"

            else:

                return "unk"

        dists = []

        for d in self.find('Root.Distribution'):

            u = Url(d.value)

            t = dist_type(u)

            if type == t:
                return Dist(t, u, d)
            elif type is False:
                dists.append(Dist(t, u, d))

        return dists
