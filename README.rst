Metatab
=======

Parse and manipulate structured data in a tabular format. 

`Metatab <http://metatab.org>`_ is a data format that allows structured information -- the sort you'd normally store in JSON, YAML or XML -- to be stored and edited in tabular forms like CSV or Excel. Metatab files look exactly like you'd expect, so they
are very easy for non technical users to read and edit, using tools they already have. Metatab is an excellt format
for creating, storing and transmitting metadata. For more information about metatab, visit http://metatab.org. 

This repository has a python module and executable. For a Javascript version, see the `metatab-js <https://github.com/CivicKnowledge/metatab-js>`_ repository.

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

The metatab python distribution includes two programs, ``metatab`` for manipulating single Metatab files  and ``metapack`` for creating data packages.


Creating a new package
----------------------

[ For an overview of the Metata format, see the `Metatab specifications <http://www.metatab.org/>`_. ]

Create a directory, usually with the name you'll give the package and create a new metatab file within it.

.. code-block:: bash

    $ mkdir example-package
    $ cd example-package
    $ metatab -c

The ``metatab -c`` command will create a new metatab file in the current directory, ``metadata.csv``. You can open this file with a spreadsheet program to edit it.

The minimum terms to enter values for are:

- Title
- Name
- Datafile

For this example, the ``Name`` term should be set to the name of the directory, 'example-package'

For the ``Datafile`` term, you can add entries directly, but it is easier to use the metapack program to add them. The ``metapack -a`` program will inspect the file for you, finding internal files in ZIP files and creating the correct URLs for Excel files.

If you have made changes to the ``metadata.csv`` file, save it, then run:

.. code-block:: bash

    $ metapack -a http://public.source.civicknowledge.com/example.com/sources/test_data.zip

The ``test_data.zip`` file is a test file with many types of tabular datafiles within it. The ``metapack -a`` command will download it, open it, find all of the data files int it, and add uRLs to the metatab. If any of the files in the zip file are Excel format, it will also create URLs for each of the tabs.

( This file is large and may take awhile. If you need a smaller file, try: http://public.source.civicknowledge.com/example.com/sources/renter_cost.csv )

Now reload the file. The Resource section should have 9 ``Datafile`` entries, all of them with fragments. The fragments will be URL encoded, so are a bit hard to read. %2F is a '/' and %3B is a ';'. The ``metatab -a`` program will also add a name, and try to get where the data starts and which lines are for headers.

Note that the ``unicode-latin1`` and ``unicode-utf8`` do not have values for StartLine and HeaderLines. This is because the row intuiting process failed to categorize the lines, because all of them are mostly strings. In these cases, download the file and examine it. For these two files, you can enter '0' for ``HeaderLines`` and '1' for ``StartLine.``

If you enter the ``Datafile`` terms manually, you should enter the URL for the datafile, ( in the cell below "Resources" ) and the ``Name`` value. If the URL to the resource is a zip file or an Excel file, you can use a URL fragment to indicate the inner filename. For Excel files, the fragment is either the name of the tab in the file, or the number of the tab. ( The first number is 0 ). If the resource is a zip file that holds an Excel file, the fragment can have both the internal file name and the tab number, seperated by a semicolon ';' For instance:

- http://public.source.civicknowledge.com/example.com/sources/test_data.zip#simple-example.csv
- http://example.com/renter_cost_excel07.xlsx#2
- http://example.com/test_data.zip#renter_cost_excel07.xlsx;B2

If you don't specify a tab name for an Excel file, the first will be used.

There are also URL forms for Google spreadsheet, S3 files and Socrata.

To test URLS, use the ``rowgen`` program:

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

Or just download the file and look at it. In this case, for both `unicode-latin1` and `unicode-utf8` you can see that the headers are on line 0 and the data starts on line 1 so enter those values into the `metadata.csv` file.

Generating Schemas
++++++++++++++++++

Now that the ``metadata.csv`` has resources specified, you can generate schemas for the resources with the `metapack -s` program.   First, save the file, then run:

.. code-block:: bash

    $ metapack -s

Re-open   ``metadata.csv`` and you should see entries for tables and columns for each of the Datafiles. After creating the schema, you should edit the description ane possible change the alternate names (``AltName`` terms. ) The alternate names are versions of the column headers that follow typical naming rules for columns. If an AltName is specified, iterating over the resource out of the package will use the AltName, rather than that column name. 


Using a Package
+++++++++++++++

At this point, the package is functionally complete, and you can check that the package is usable. First, list the resources with :

.. code-block:: bash

    $ metatab -R metadata.csv
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

    $ metatab -R metadata.csv#simple-example

You can also read the resources from a Python program, with an easy way to convert a resource to a Pandas DataFrame

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
    
Making Other Package Formats
++++++++++++++++++++++++++++

The tutorial above is actually creating a data package in a directory. There are several other forms of packages that Metapack can create including Excel, ZIP and S3.


.. code-block:: bash

    $ metatab -e # Make an Excel package, example-package.xlsx
    $ metatab -z # Make a ZIP package, example-package.zip
    
The Excel package, ``example-package.xlsx`` will have the Metatab metadata from metata.csv in the ``Meta`` tab, and will have one tab per resource from the Resoruces section. The ZIP package ``example-package.zip`` will have all of the resources in the ``data`` directory and will also include the metadata in Tabulr Data Package format in the ``datapackage.json`` file. You can interate over the resoruces in these packages too:

.. code-block:: bash

    $ metatab -R example-package.xlsx#simple-example
    $ metatab -R example-package.zip#simple-example 

.. code-block:: python 

    import metatab

    doc = metatab.open_package('example-package.zip') 
    # Or
    doc = metatab.open_package('example-package.xlsx') 
    

    
