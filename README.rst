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

    $ pip install https://github.com/CivicKnowledge/metatab.git

Then test parsing using a remote file with:

.. code-block:: bash

    $ metatab -j https://raw.githubusercontent.com/CivicKnowledge/metatab/master/test-data/example1.csv

Run ``metatab -h`` to get other program options.

The ``test-data`` directory has test files that also serve as examples to parse. You can either clone the repo and parse them from the files, or from the Github page for the file, click on the ``raw`` button to get raw view of the flie, then copy the URL.

