Metatab
=======

Parse and manipulate structured data in a tabular format. 

`Metatab <http://metatab.org>`_ is a data format that allows structured information -- the sort you'd normally store in JSON, YAML or XML -- to be stored and edited in tabular forms like CSV or Excel. Metatab files look exactly like you'd expect, so they
are very easy for non technical users to read and edit, using tools they already have. Metatab is an excellt format
for creating, storing and transmitting metadata. For more information about metatab, visit http://metatab.org. 

This repository has a python module and executable. For a Javascript version, see the `metatab-js <https://github.com/CivicKnowledge/metatab-js>`_ repository.

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

