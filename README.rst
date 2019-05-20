Metatab
=======

.. image:: https://travis-ci.org/Metatab/metatab.svg?branch=master
    :target: https://travis-ci.org/Metatab/metatab

Parse and manipulate structured data and metadata in a tabular format.

`Metatab <http://metatab.org>`_ is a data format that allows structured
metadata -- the sort you'd normally store in JSON, YAML or XML -- to be stored
and edited in tabular forms like CSV or Excel. Metatab files look exactly like
you'd expect, so they are very easy for non-technical users to read and edit,
using tools they already have. Metatab is an excellent format for creating,
storing and transmitting metadata. For more information about metatab, visit
http://metatab.org.

This repository has a Python module and executable. For a Javascript version,
see the `metatab-js <https://github.com/CivicKnowledge/metatab-js>`_ repository.

What is Metatab For?
--------------------

Metatab is a tabular format that allows storing metadata for demographics,
health and research datasets in a tabular format. The tabular format is much
easier for data creators to write and for data consumers to read, and it allows
a complete data packages to be stored in a single Excel file.


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

The ``test-data`` directory has test files that also serve as examples to
parse. You can either clone the repo and parse them from the files, or from the
Github page for the file, click on the ``raw`` button to get raw view of the
flie, then copy the URL.


Running tests
+++++++++++++

Run ``python setup.py tests`` to run normal development tests. You can also run
``tox``, which will try to run the tests with python 3.4, 3.5 and 3.6, ignoring
non-existent interpreters.


Development Testing with Docker
+++++++++++++++++++++++++++++++

Testing during development for other versions of Python is a bit of a pain,
since you have to install the alternate version, and Tox will run all of the
tests, not just the one you want.

One way to deal with this is to install Docker locally, then run the docker
test container on the source directory. This is done automatically from the
Makefile in metatab/test, just run:

.. code-block:: bash

    $ cd metatab/test
    $ make build # to create the container image
    $ make test
    # or just ..
    $ make

You can also run the container shell, and run tests from the command line.

.. code-block:: bash

    $ cd metatab/test
    $ make build # to create the container image
    $ make shell # to run bash the container

You now have a docker container where the /code directory is the metatab source dir.

Now, run tox to build the tox virtual environments, then enter the specific version you want to
run tests for and activate the virtual environment.

.. code-block:: bash

    # tox
    # cd .tox/py34
    # source bin/activate # Activate the python 3.4 virtual env
    # cd ../../
    # python setup.py test # Cause test deps to get installed
    #
    # python -munittest metatab.test.test_parser.TestParser.test_parse_everython  # Run one test

Note that your development environment is mounted into the Docker container, so you can edit local
files and test the changes in Docker.






