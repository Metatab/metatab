
Row Generating Programs
=======================

Metatab Datafile terms can reference programs and IPython notebooks to generate rows. 

To reference a program, the ``Root.Datafile`` must be a URL with a ``program`` scheme and a relative path. Usually, the file is placed in a subdirectory named 'scripts' at the same level as the ``metadata.csv`` file. It must be an executable program, and may be any executable program. 

When a data package is created, regardless of the type, a filesystem package is created first, then other types of packages are created from the filesystem package. This means that the row-generating program is only run once per resource when multiple packages are created, and also that the program can open the Metatab package being used to run the program to access previously created resource files. 

Program Inputs
**************

The program can receive information from Metatab through program options and environmental variables, and must print CSV formatted lines to std out. 

There are two broad sources for inputs to the program. The first is are several values that are passed into the program regardless of the configuration of the ``Root.DataFile`` term. The second are the properties of the ``Root.DataFile`` terms. 

The inputs for all programs are: 

- METATAB_DOC: An env var that holds the URL for the Metatab document being processed
- METATAB_PACKAGE: An env var that holds the metatab document's package URL. ( Which is usually the same as the document URL )
- METATAB_WORKING_DIR: An env var that holds the path to the directory holding the metatab file. 
- PROPERTIES: An env var with holds a JSON encoded dict with the three previous env values, along with the ``properties`` dict for the ``Root.DataFile`` term. 

Additionally, the program receives the ``Root.DataFile`` properties in these forms:

- Properties that have names that are all uppercased are assigned to env variables. 
- Properties that have names that begin with '-' are assigned to program options.


Common Patterns
***************

It is very common for a program to open the Metatab document that is being used to run the program. In Python:

.. code-block:: python 

    import metatab as mt
    doc = mt.MetatabDoc(environ['METATAB_DOC'])

Since the program must output CSV formatted lines, a CSV writer can be constructed on ``sys.stdout``:

.. code-block:: python 

     import sys
     import csv
     
     w = csv.writer(sys.stdout)
     
     w.writerow(...)
     
     
If the program generates logging or warnings, they must be printed to ``sys.stderr``

.. code-block:: python 

     import sys
     
     print("ERROR!", file=sys.stderr)
     
     