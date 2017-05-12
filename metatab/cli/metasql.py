# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Load a resource into an Sql database.
"""


# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
CLI program for storing pacakges in CKAN
"""

import sys

from metatab import _meta, DEFAULT_METATAB_FILE, resolve_package_metadata_url, MetatabDoc
from metatab.util import slugify
from os import getcwd
from os.path import join
from rowgenerators import Url, get_cache
from sqlalchemy import String, Integer, Float
from sqlalchemy import Table, Column
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import create_session
from .core import prt, err

class MetapackCliMemo(object):
    def __init__(self, args):
        self.cwd = getcwd()
        self.args = args
        self.cache = get_cache('metapack')

        self.urls = args.urls
        print(self.urls)

        sqlalchemy_schemes = ' postgresql mysql oracle sqlite oracle '.split()

        for url in args.urls:
            u = Url(url)

            if u.proto in sqlalchemy_schemes or u.scheme in sqlalchemy_schemes:
                self.db_url = url
            else:
                self.metatabfile = url


        if  self.metatabfile and  self.metatabfile.startswith('#'):
            # It's just a fragment, default metatab file
            self.metatabfile = join(self.cwd, DEFAULT_METATAB_FILE) + self.metatabfile

        self.mtfile_arg =  self.metatabfile if self.metatabfile else join(self.cwd, DEFAULT_METATAB_FILE)

        self.mtfile_url = Url(self.mtfile_arg)

        self.resource = self.mtfile_url.parts.fragment

        self.package_url, self.mt_file = resolve_package_metadata_url(self.mtfile_url.rebuild_url(False, False))



class Database(object):

    def __init__(self, db_url):

        self.db_url = db_url

        self.engine = create_engine(db_url)
        self.metadata = MetaData(bind=self.engine)
        self.session = create_session(bind=self.engine, autocommit=False, autoflush=True)

    def list_tables(self):
        from sqlalchemy.engine import reflection

        inspector = reflection.Inspector.from_engine(self.engine)

        for table_name in inspector.get_table_names():
            yield table_name

    def has_table(self, table_name):
        return table_name in list(self.list_tables())
        return self.engine.dialect.has_table(self.engine, table_name)

    def delete_table(self, table_name):

        t = Table(table_name,self.metadata)
        t.drop(self.engine)

        self.metadata = MetaData(bind=self.engine)

    def make_table(self, table_name, columns):


        type_map = {
            'text': String,
            'number': Float,
            'integer': Integer
        }

        sacolumns = []

        for c in columns:
            sacol = Column(c['name'], type_map.get(c['datatype'], String)())

            sacolumns.append(sacol)

        table = Table(table_name, self.metadata, Column('_id', Integer, primary_key=True), *sacolumns)

        table.create()

    def get_table(self, table_name):

        return Table(table_name, self.metadata, autoload=True, autoload_with=self.engine)

    def bulk_insert(self, table_name, rows):

        table = self.get_table(table_name)

        self.engine.execute(table.insert(), rows)


def metasql():
    import argparse
    parser = argparse.ArgumentParser(
        prog='metasql',
        description='Load a metatab resource into a relational database'.format(_meta.__version__),
    )

    parser.add_argument('-i', '--info', default=False, action='store_true',
                        help="Show configuration information")

    parser.add_argument('-l', '--list-tables', action='store_true', default=False,
                        help='List tables in the database and exist')

    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help="For some commands, be more verbose")

    parser.add_argument('-A', '--append', action='store_true', default=False,
                        help='Append data to an existing table')

    parser.add_argument('-D', '--delete-table', action='store_true', default=False,
                             help='Delete a table if it already exists')

    parser.add_argument('urls', nargs='*', help='Path to a Metatab file')

    m = MetapackCliMemo(parser.parse_args(sys.argv[1:]))


    print(m.mt_file)
    print(m.db_url)


    db = Database(m.db_url)

    if m.args.list_tables:
        for t in db.list_tables():
            prt(t)
        sys.exit(0)

    doc = MetatabDoc(m.mt_file)

    if m.resource:
        make_table(m, doc, m.resource, db)
        insert_data(m, doc, m.resource, db)

    else:
        # Here we should install all of the datasets.
        pass


def make_table_name(doc, resource_name):
    """Create a table name that include the dataset name and the resource name"""

    r = doc.resource(name=resource_name)

    st, _ = r.schema_term

    dataset = doc.find_first_value('Root.Dataset')

    if not dataset:
        dataset = doc.find_first_value('Root.Name')

    if not dataset:
        err("Failed to get either Root.Dataset or Root.Name")

    return slugify('{}-{}'.format(dataset, st.value)).replace('-', '_')


def make_table(m, doc, resource_name, db):

    table_name = make_table_name(doc, resource_name)

    table_exists = db.has_table(table_name)

    if  table_exists:
        if m.args.delete_table:
            prt("Deleting table '{}' ".format(table_name))
            db.delete_table(table_name)
        else:
            err("Table '{}' already exists".format(table_name))
            return False

    r = doc.resource(name=resource_name)

    db.make_table( table_name, r.columns())

    return True

def insert_data(m, doc, resource_name, db):

    table_name = make_table_name(doc, resource_name)

    r = doc.resource(name=resource_name)

    rows = list(r.iterdict)

    db.bulk_insert(table_name, rows)

