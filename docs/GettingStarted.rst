Metatab
=======

Parse and manipulate structured data and metadata in a tabular format.

`Metatab <http://metatab.org>`_ is a data format that allows structured metadata -- the sort you'd normally store in JSON, YAML or XML -- to be stored and edited in tabular forms like CSV or Excel. Metatab files look exactly like you'd expect, so they
are very easy for non-technical users to read and edit, using tools they already have. Metatab is an excellent format
for creating, storing and transmitting metadata. For more information about metatab, visit http://metatab.org.

This repository has a Python module and executable. For a Javascript version, see the `metatab-js <https://github.com/CivicKnowledge/metatab-js>`_ repository.

What is Metatab For?
--------------------

Metatab is a tabular format that allows storing metadata for demographics, health and research datasets in a tabular format. The tabular format is much easier for data creators to write and for data consumers to read, and it allows a complete data packages to be stored in a single Excel file.


Install
-------

Install the package from PiPy with:

.. code-block:: bash

    $ pip install metatab

Or, install the master branch from github with:

.. code-block:: bash

    $ pip install https://github.com/CivicKnowledge/metatab-py.git

Then test parsing using a remote file with:

.. code-block:: bash

    $ metatab -j https://raw.githubusercontent.com/CivicKnowledge/metatab-py/master/test-data/example1.csv

Run ``metatab -h`` to get other program options. 

The ``test-data`` directory has test files that also serve as examples to parse. You can either clone the repo and parse them from the files, or from the Github page for the file, click on the ``raw`` button to get raw view of the flie, then copy the URL.


Metatab and Metapack
--------------------

The metatab Python distribution includes two programs, ``metatab`` for manipulating single Metatab files  and ``metapack`` for creating data packages. The two programs share some options, so when building packages, you can use the ``metapack`` program exclusively, and ``metatab`` is most useful for converting Metatab files to JSON. This tutorial will primarily use ``metapack``


Creating a new package
----------------------

[ For an overview of the Metatab format, see the `Metatab specifications <http://www.metatab.org/>`_. ]

Create a directory, usually with the name you'll give the package and create a new metatab file within it.

.. code-block:: bash

    $ mkdir example-data-package
    $ cd example-data-package
    $ metapack -c

The ``metapack -c`` command will create a new Metatab file in the current directory, ``metadata.csv``. You can open this file with a spreadsheet program to edit it.

Tne only required term to set is ``Name``, but you should have values for ``Title`` and ``Description.`` Initially, the ``Name`` is set to the same values as ``Identity``, which is set to a randuom UUID4. 

For this example, the ``Name`` term could be changed to the name of the directory, 'example-package.' However, it is more rigorous to set the name component terms, ``DatasetName`` and zero or more of ``Origin``, ``Version``, ``Time`` or ``Space``. These terms will be combined to make the name, and the name will include important components to distinguish different package versions and similar datasets from different sources. The ``Name`` term is used to generate files names when making ZIP, Excel and S3 packages. For this tutorial use these values:

- Dataset: 'example-data-package'
- Origin ( in the 'Contacts' Section): 'example.com'
- Version ( Automatically set ) : '1'
- Space: 'US'
- Time: '2017'

 These values will generate the name 'example.com-example_data_package-2017-us-1'. If you update the package, change the ``Version`` value and run ``metapack -u`` to regenerate the ``Name``.

After setting the ``DatasetName``, ``Origin``, ``Version``, ``Time`` or ``Space`` and saving the file, , run ``metapack -u`` to update ``Name``:

.. code-block:: bash

    $ metapack -u
    Updated Root.Name to: 'example.com-example_data_package-2017-us-1' 

Since this is a data package, it is important to have references to data. The package we are creating here is a filesystem package, and will usually reference the URLs to data on the web. Later, we will generate other packages, such as ZIP or Excel files, and the data will be downloaded and included directly in the package. We define the paths or URLs to data files with the ``DataFile`` term. 

For the ``Datafile`` term, you can add entries directly, but it is easier to use the ``metapack`` program to add them. The ``metapack -a`` program will inspect the file for you, finding internal files in ZIP files and creating the correct URLs for Excel files.

If you have made changes to the ``metadata.csv`` file, save it, then run:

.. code-block:: bash

    $ metapack -a http://public.source.civicknowledge.com/example.com/sources/test_data.zip

The ``test_data.zip`` file is a test file with many types of tabular datafiles within it. The ``metapack -a`` command will download it, open it, find all of the data files int it, and add URLs to the metatab. If any of the files in the zip file are Excel format, it will also create URLs for each of the tabs.

( This file is large and may take awhile. If you need a smaller file, try: http://public.source.civicknowledge.com/example.com/sources/renter_cost.csv )

The ``metapack -a`` command also works on directories and webpages. For instance, if you wanted to scrape all of the 60 data files for the California English Language Development Test, you could run: 

.. code-block:: bash

    metapack -a http://celdt.cde.ca.gov/research/admin1516/indexcsv.asp

Now reload the file. The Resource section should have 9 ``Datafile`` entries, all of them with fragments. The fragments will be URL encoded, so are a bit hard to read. %2F is a '/' and %3B is a ';'. The ``metatab -a`` program will also add a name, and try to get where the data starts and which lines are for headers.

Note that the ``unicode-latin1`` and ``unicode-utf8`` do not have values for StartLine and HeaderLines. This is because the row intuiting process failed to categorize the lines, because all of them are mostly strings. In these cases, download the file and examine it. For these two files, you can enter '0' for ``HeaderLines`` and '1' for ``StartLine.``

If you enter the ``Datafile`` terms manually, you should enter the URL for the datafile, ( in the cell below "Resources" ) and the ``Name`` value. If the URL to the resource is a zip file or an Excel file, you can use a URL fragment to indicate the inner filename. For Excel files, the fragment is either the name of the tab in the file, or the number of the tab. ( The first number is 0 ). If the resource is a zip file that holds an Excel file, the fragment can have both the internal file name and the tab number, separated by a semicolon ';' For instance:

- http://public.source.civicknowledge.com/example.com/sources/test_data.zip#simple-example.csv
- http://example.com/renter_cost_excel07.xlsx#2
- http://example.com/test_data.zip#renter_cost_excel07.xlsx;B2

If you don't specify a tab name for an Excel file, the first will be used.

There are also URL forms for Google spreadsheet, S3 files and Socrata.

To test manually added URLs, use the ``rowgen`` program, which will download and cache the URL resource, then try to interpret it as a CSV or Excel file. 

.. code-block:: bash

    $ rowgen http://public.source.civicknowledge.com/example.com/sources/test_data.zip#renter_cost_excel07.xlsx

    ------------------------  ------  ----------  ----------------  ----------------  -----------------
    Renter Costs
    This is a header comment

                                      renter                        owner
    id                        gvid    cost_gt_30  cost_gt_30_cv     cost_gt_30_pct    cost_gt_30_pct_cv
    1.0                       0O0P01  1447.0      13.6176070904818  42.2481751824818  8.27214070699712
    2.0                       0O0P03  5581.0      6.23593207100335  49.280353200883   4.9333693053569
    3.0                       0O0P05  525.0       17.6481586482953  45.2196382428941  13.2887199930555
    4.0                       0O0P07  352.0       28.0619645779719  47.4393530997305  17.3833286873892


( As of metatab 1.8, rowgenerator 0.0.7, some files with encodings that are not ascii or utf-8 will fail for Python2, but will work for Python3. )

Or just download the file and look at it. In this case, for both `unicode-latin1` and `unicode-utf8` you can see that the headers are on line 0 and the data starts on line 1 so enter those values into the `metadata.csv` file. Setting the ``StartLine`` and ``HeaderLines`` values is critical for properly generating schemas. 

Generating Schemas
++++++++++++++++++

Before generating schemas, be sure that the ``StartLine`` and ``HeaderLines`` properties are set for every ``DataFile`` term.

Now that the ``metadata.csv`` has resources specified, you can generate schemas for the resources with the `metapack -s` program.   First, save the file, then run:

.. code-block:: bash

    $ metapack -s

Re-open  ``metadata.csv`` and you should see entries for tables and columns for each of the Datafiles. After creating the schema, you should edit the description ane possible change the alternate names (``AltName`` terms. ) The alternate names are versions of the column headers that follow typical naming rules for columns. If an AltName is specified, iterating over the resource out of the package will use the AltName, rather than that column name. 


Using a Package
+++++++++++++++

At this point, the package is functionally complete, and you can check that the package is usable. First, list the resources with :

.. code-block:: bash

    $ metapack -R metadata.csv
    random-names http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Frandom-names.csv
    renter_cost http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Frenter_cost.csv
    simple-example-altnames http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Fsimple-example-altnames.csv
    simple-example http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Fsimple-example.csv
    unicode-latin1 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Funicode-latin1.csv
    unicode-utf8 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fcsv%2Funicode-utf8.csv
    renter_cost_excel07 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fexcel%2Frenter_cost_excel07.xlsx%3BSheet1
    renter_cost_excel97 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Fexcel%2Frenter_cost_excel97.xls%3BSheet1
    renter_cost-2 http://public.source.civicknowledge.com/example.com/sources/test_data.zip#test_data%2Ftab%2Frenter_cost.tsv

You can dump one of the resources as a CSV by running the same command with the resource name as a fragment to the name of the metatab file:

.. code-block:: bash

    $ metapack -R metadata.csv#simple-example

or:

.. code-block:: bash

    $ metapack -R "#simple-example"

You can also read the resources from a Python program, with an easy way to convert a resource to a Pandas DataFrame.

.. code-block:: python 

    import metatab

    doc = metatab.open_package('.')  # Will look for 'metadata.csv'

    print(type(doc))

    for r in doc.resources():
        print(r.name, r.url)
    
    r = doc.first_resource('renter_cost')

    # Dump the row
    for row in r:
        print row


    # Or, turn it into a pandas dataframe
    # ( After installing pandas ) 
    
    df = doc.first_resource('renter_cost').dataframe()

For a more complete example, see `this Jupyter notebook example <https://github.com/CivicKnowledge/metatab/blob/master/examples/Access%20Examples.ipynb>`_

Making Other Package Formats
++++++++++++++++++++++++++++

The tutorial above is actually creating a data package in a directory. There are several other forms of packages that Metapack can create including Excel, ZIP and S3.


.. code-block:: bash

    $ metapack -e # Make an Excel package, example.com-example_data_package-2017-us-1.xlsx
    $ metapack -z # Make a ZIP package, example.com-example_data_package-2017-us-1.zip

The Excel package, ``example-package.xlsx`` will have the Metatab metadata from metata.csv in the ``Meta`` tab, and will have one tab per resource from the Resources section. The ZIP package ``example-package.zip`` will have all of the resources in the ``data`` directory and will also include the metadata in `Tabular Data Package <http://specs.frictionlessdata.io/tabular-data-package/>`_ format in the ``datapackage.json`` file. You can interate over the resources in these packages too:

.. code-block:: bash

    $ metapack -R example.com-example_data_package-2017-us-1.zip#simple-example
    $ metapack -R example.com-example_data_package-2017-us-1.xlsx#simple-example

The ``metapack -R`` also works with URLs:

.. code-block:: bash

    $ metapack -R http://devel.metatab.org/excel/example.com-example_data_package-2017-us-1.xlsx#simple-example
    $ metapack -R http://devel.metatab.org/excel/example.com-example_data_package-2017-us-1.zip#simple-example

And, you can access the packages in Python:


.. code-block:: python 

    import metatab

    doc = metatab.open_package('example-package.zip') 
    # Or
    doc = metatab.open_package('example-package.xlsx') 
    
Note that the data files in a derived package may be different that the ones in the source directory package. The derived data files will always have a header on the first line and data starting on the second line. The header will be taken from the data file's schema, using the ``Table.Column`` term value as the header name, or the ``AltName`` property, if it is defined. The names are always "slugified" to remove characters other than '-', '_' and '.' and will always be lowercase, with initial numbers removed.

If the ``Datafile`` term has a ``StartLine`` property, the values will be used in generating the data in derived packages to select the first line for yielding data rows. ( The ``HeaderLines`` property is used to build the schema, from which the header line is generated. )
    
Publishing Packages
-------------------

The ``metasync`` program can build multiple package types and upload them to an S3 bucket. Typical usage is: 

.. code-block:: bash

    $ metasync -c -e -f -z -s s3://library.metatab.org
    
With these options, the ``metasync`` program will create an Excel, Zip and Filesystem package and store them in the s3 bucket ``library.metadata.org``. In this case, the "filesystem" package is not created in the local filesystem, but only in S3. ( "Filesystem" packages are basically what you get after unziping a ZIP package. )

Because generating all of the packages and uploading to S3 is common, the `metasync -S` option is a synonym for generating all package types and uploading:

.. code-block:: bash

    $ metasync -S s3://library.metatab.org

Currently, ``metasync`` will only write packages to S3. For S3 ``metasync`` uses boto3, so refer to the `boto3 credentials documentation <http://boto3.readthedocs.io/en/latest/guide/configuration.html>`_ for instructions on how to set your S3 access key and secret. 

One important side effect of the ``metasync`` program is that it will add ``Distribution`` terms to the main ``metadata.csv`` file before creating the packages, so all the packages that the program syncs will include references to the S3 location of all packages. For instance, the example invocation above will add these ``Distribution`` terms: 

.. code-block:: 

    Distribution	http://s3.amazonaws.com/library.metatab.org/simple_example-2017-us-1.xlsx
    Distribution	http://s3.amazonaws.com/library.metatab.org/simple_example-2017-us-1.zip
    Distribution	http://s3.amazonaws.com/library.metatab.org/simple_example-2017-us-1/metadata.csv
    
These ``Distribution`` terms are valuable documentation, but they are also required for the ``metakan`` program to create entries for the package in CKAN. 



Adding Packages to CKAN
+++++++++++++++++++++++

The ``metakan`` program reads a Metatab file, creates a dataset in CKAN, and adds resources to the CKAN entry based on the ``Distribution`` terms in the Metatab data. For instance, with a localhost CKAN server, and the metadata file from the "Publishing Packages" section example: 

.. code-block:: bash

    $ metakan  --ckan http://localhost:32768/ --api f1f45...e9a9

This command would create a CKAN dataset with the metadata in the ``metadata.csv`` file in the current directory, reading the ``Distribution`` terms. It would add resources for ``simple_example-2017-us-1.xlsx`` and ``simple_example-2017-us-1.zip.`` For the ``simple_example-2017-us-1/metadata.csv`` entry, it would read the remote ``metadata.csv`` file, resolve the resource URLs, and create a resource entry in CKAN for the ``metadata.csv`` file and all of the resources referenced in the remote ``metadata.csv`` file. 

Note that because part of the information in the CKAN dataset comes from the loal ``metadata.csv`` file and part of the resources are discovered from the remote file, there is a substantial possibility for these files to become unsynchronized. For this reason, it is important to run the ``metasync`` program to create ``Distribution`` terms before running the ``metakan`` program. 

For an example of a CKAN entry generated by ``metakan``, see http://data.sandiegodata.org/dataset/fns-usda-gov-f2s_census-2015-2

Publish to CKAN from S3
.......................

The ``metakan`` program can publish all of the CSV packages available in an S3 bucket by giving it an S3 url instead of a Metatab file. For instance, to publish all of the CSV packages in the ``library.metatab.org `` bucket, run:

.. code-block:: bash

    $ metakan  --ckan http://localhost:32768/ --api f1f45...e9a9 s3://library.metatab.org

As with publishing a local Metatab file, the CSV packages in the S3 buck may have ``Distribution`` terms to identify other packages that should also be published into the CKan dataset.



Adding Packages to Data.World
+++++++++++++++++++++++++++++

The ``metaworld`` program will publish the package to `Data.World <http://data.world>`_.  Only Excel and CSV packages will be published, because ZIP packages will be disaggregated, conflicting with CSV packages. The program is a bit buggy, and when creating a new package, the server may return a 500 error. If it does, just re-run the program.

The ``metaworld`` program takes no options. To use it, you must install the `datadotworld python package <https://github.com/datadotworld/data.world-py>`_ and configure it, which will store your username and password.


.. code-block:: bash

    $ metaworld


Publishing With Docker
++++++++++++++++++++++

The time require to run ``metasync`` to build and publish packages is often limited by network bandwidth, and can be much faster if run from a hosting service with a high bandwith connection, like AWS EC2. The ``metasync`` supports remote operation with the ``--docker`` option, which will re-run the program in docker.

To build the docker container, run ``make build`` in the ``docker`` directory in this github repository. Then add the ``-D`` or ``--docker`` option to the ``metasync`` command. The metatab document must be explicit, and must be acessible from the network.

.. code-block:: bash

    $ metasync -D -S s3://library.metatab.org http://devel.metatab.org/example.com-simple_example-2017-us-1.csv


