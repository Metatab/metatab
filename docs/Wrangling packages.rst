Guide to Wrangling Metatab Packages
===================================


Setting the Name
----------------

For any non-trivial use, the ``Root.Name`` term is critical; most Metatab programs require it to be set. It can be set directly, but it is much more useful to allow ``metapack`` to set it, by aggregating other terms. The other terms that ``metapack`` will combine to create a name are:

- Dataset. The base name of the dataset.
- Origin. A part of a domain name ( like 'usgs.gov' or 'census.gov' ) for the source of the data.
- Version. An integer version number
- Space. The name of the region that the data covers. 
- Time. A year, year range, or other time interval for the temporal coverage of the data. 
- Grain. The name of what each row is about, such as a 'school' or a 'county' or a 'person'

The ``Space``, ``Time`` and ``Grain`` are usually only used to distinguishing this package from other packages. If there is only one package for a particular ``Dataset`` value, these three terms are rarely used. 

Setting the ``Dataset`` term triggers rebuilding the ``Name`` term; if ``Dataset`` is not set, ``metapack`` will not update the ``Name`` term. You can run ``metapack -u`` to force regenerating the name.

Adding Properties to Sections
-----------------------------

``Root.Section`` terms introduce Sections, which both group terms and set the headings for term properties. In the Section row, all of the values in the 3rd and later columns set the property name for child property terms. For instance, the default ``Schema`` section is:

::

    A       B       C           D       E
    Section	Schema	DataType	AltName	Description

The B column is the section name, and the C, D, and E columns cause the parser to interpret values in those columns as being child values of terms on the row, with a term name given by the header in the ``Section`` Line. So, for a row that starts with a ``Table.Column`` term, the value in the C column is the value for a ``Column.DataType`` property.

You can re-order these header values, and can create new ones, but in some cases, the ``metapack`` program will expect some properties to exist. For instance, every ``Table.Column`` term must have a ``Column.DataType`` term.


Groups and Tags
---------------

When creating entries in a data repository like CKAN or Data.World, the ``metakan`` and ``metaworld`` programs  may categorize the dataset entry with groups and tags. Metatab treats these term values as simple strings, so refer to the data repository documentation for specifics about how groups and tags are used.

For Tags, set a value for the ``Root.Tag`` and  for groups, use ``Root.group``


Schemas
-------

Schemas are the ``Root.Table`` terms in the ``Schema`` section of the metatab document, along with it's ``Table.Column`` children. The value of the ``Root.Table`` term is the name of the schema, and this value can be referenced from the ``Root.DataSet`` entries in the ``Resources`` section either by being set to the ``Dataset.Name`` for the entry, or by being set as the ``Dataset.Schema``. Using ``Dataset.Name`` is the default case, but using this method of linking only allows one resource per schema. If there are multiple resources that should share the same schema, link the two with the ``Dataset.Schema`` property.


Column Names
++++++++++++

The value of a ``Table.Column`` term is the primary name of a column, most often the column header from the original resource.

The ``Column.AltName`` term sets and alternate name for the column, which will be used whenever the resource is copied into a new package. The alterate name is set when the primary name is not a well formed column name. For instance, if the header value from the original resource is 'Date & Time', the ``Table.Column`` value will be 'Date & Time', but 'Column.AltName' will also be set and will be 'date_time'.

When a resource is copied, such as building a package with ``metatab`` or ``metasync``, the data file will have the header value from ``Column.AltName`` when it exists and from ``Table.Column`` when it doesn't. The header values will be moved into the new package's schema as  in the ``Table.Column`` values. Because all of the ``Column.AltName`` values will have been "made official" when packaging, the Altname column is removed from the schema after packaging.

Because the header can come from either  ``Column.AltName`` or  `Table.Column`` values, you only need to set the ``Column.AltName`` when the `Table.Column`` value is an ill-formed header.


DataTypes
+++++++++

Every ``Table.Column`` term must have a ``Column.Datatype`` to be useful. The values for these terms are free-form, but most processing programs will expect them to be one of:

::

  integer
  number
  text

These are the same values as are used in Tabular Data Packages. The value of `number` is a general real or floating point number.

Testing Packages
----------------

When you are working on a package where the ``metadata.csv`` file is stored on Github or a similar VCS system, you are working on a "source" Metatab file, since the Metatab file will directly reference data files. To test that the file is what you want, you should occasionally build a filesystem package from this file, using ``metatab -F -f``. The ``-F`` option will force the new package to be build, although if you want  be completely sure, you can delete the ``_packages`` directory in the current directory.

The first tests should be done by building the package, then inspecting the data files to see that they have the columns that you expect. Then open the ``index.html`` file to ensure that all of the documentation you want has been generated.

When the package looks correct from direct inspection, you can open it in Jupyter Notebook to check the documentation.

Start Jupyter Notebook in the current directory, with the source ``metadata.csv`` file. Then enter this in a cell:

.. code-block:: python

    import metatab
    doc = metatab.open_package('./metadata.csv')
    doc

You should get a pretty HTML version of the package documentation. Alternately, you can dump the docs for the package and the data dictoinaries for all of the resource with:

.. code-block:: python

    import metatab
    from IPython.display import display_html

    doc = metatab.open_package('./metadata.csv')
    display_html(doc)

    for r in doc.resources():
        display_html(r)


The previous code is displaying the documentation generated from the source Metatab document. You may also want to view the documentation generated form the file system package you build with `metapack -F -f`. In that case, open the package document with:

.. code-block:: python

    doc = metatab.open_package('./_packages/<package_name>/')

The result should be the same documentation, but with different URLs.