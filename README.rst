Metatab
=======

Parse and manipulate a Structured Tabluar File

Install the package with:

.. code-block:: bash

    $ pip install metatab

.. code-block:: bash

    $ pip install https://github.com/CivicKnowledge/metatab-py.git

Then test parsing using a remote file with:

.. code-block:: bash

    $ metatab -j https://raw.githubusercontent.com/CivicKnowledge/metatab-py/master/test-data/children.csv


Parsing Metatab Files
---------------------

The ``test-data`` directory has test files that also serve as examples to parse.



Running a Metatab Server in Docker
----------------------------------

The ``docker`` directory contains Dockerfiles and Makefiles to operate them. The numbers ane redis containers are needed
only for production systems and the Google Spreadsheet plugin that generate ID numbers; you can safely ignore them.

To build and run the test metatab container:

.. code-block:: bash

    $ cd docker/metatab
    $ make build
    $ make start
    $ ./test.sh

