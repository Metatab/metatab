# Copyright (c) 2016 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

def write_excel_partition(p, path):
    """Write a partition to an excel file."""
    from openpyxl import Workbook
    import string

    wb = Workbook(write_only=True)

    ws = wb.create_sheet()
    ws.title = "data"
    ws.sheet_properties.tabColor = "88ff88"

    ws.append([c.name for c in p.table.columns])

    for row in p:
        ws.append(list(row.values()))

    ws = wb.create_sheet()
    ws.title = "meta"
    ws.sheet_properties.tabColor = "8888ff"

    ws.append(('property','value'))
    ws.append(('title', p.name))
    ws.append(('description', p.description))

    ws = wb.create_sheet()
    ws.title = "schema"
    ws.sheet_properties.tabColor = "ff8888"

    ws.append(('Section', 'Schema', 'datatype', 'description'))

    ws.append(('Table', p.table.name))

    for c in p.table.columns:
        ws.append(('Column', c.name, c.valuetype, c.description))

    wb.save(path)

def write_excel(path, builder):
    from openpyxl import Workbook
    import string
    from os.path import join

    wb = Workbook(write_only=True)
    ws = wb.create_sheet()
    ws.title = "meta"
    ws.sheet_properties.tabColor = "8888ff"

    for row in builder.rows:
        ws.append(row)



    #ws.append(('Format', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    wb.save(path)