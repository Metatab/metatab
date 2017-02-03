#!/usr/bin/env python
#
# Create a Metatab file for the 2014 American Community Survey, 5 year release.
# This program requires Ambry, along with several Ambry datasets.
#

from ambry import get_library
from metatab.doc import MetatabDoc
from collections import defaultdict

l = get_library()
table_meta_p = l.partition('census.gov-acs_geofile-schemas-2009e-table_meta-2014-5')
column_meta_p = l.partition('census.gov-acs_geofile-schemas-2009e-column_meta-2014-5')

sequence_p = l.partition('census.gov-acs_geofile-schemas-2009e-table_sequence-2014-5')
sequences = {row.table_id: (row.sequence_number, row.start, row.table_cells)
             for row in sequence_p if row.start}

root_doc = MetatabDoc()
root = root_doc.new_section('Root')

root.new_term('Declare', 'http://assets.metatab.org/census.csv')
root.new_term('Title', 'American Community Survey, 5 Year, 2009-2014')
root.new_term('Release', 5)
root.new_term('Year', 2014)
root.new_term('Include', 'acs20145-sources.csv')
root.new_term('Include', 'acs20145-schema.csv')

root_doc.write_csv('acs20145-metadata.csv')

src_doc = MetatabDoc()
source_sec = src_doc.new_section('Sources', ['geography', 'state'])

from censuslib import ACS09TableRowGenerator as TableRowGenerator

b = l.bundle('census.gov-acs-p5ye2014')
b = b.cast_to_subclass()
s = b.source('b00001')  # Any source will do

trg = TableRowGenerator(b, s)

for s1, s2 in trg.generate_source_refs():
    # S1 and S2 are for the estimates and margins file,
    # so we nly need one of them

    source_sec.new_term('Datafile', s1['url'],
                        geography=s1['size'],
                        state=s1['stusab'])

src_doc.write_csv('acs20145-sources.csv')

sch_doc = MetatabDoc()

sch = sch_doc.new_section('Schema', 'title column_ref indent'.split())

tables = defaultdict(dict)

for t in table_meta_p:
    sq = sequences[t.table_id]
    tables[t.table_id] = sch.new_term('Table', t.table_id,
                                      title=t.table_title,
                                      subject=t.subject_area,
                                      universe=t.universe,
                                      column_ref=t.denominator_column_id,
                                      topics=t.topics,
                                      segment=sq[0],
                                      startcol=sq[1],
                                      colwidth=sq[2])

for c in column_meta_p:
    t = tables[c.table_id]

    t.new_child('Column', c.column_id,
                title=c.column_title,
                column_ref=c.parent_column_id,
                indent=c.indent
                )

sch_doc.write_csv("acs20145-schema.csv")