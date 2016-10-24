Metatab
=======

Parse and manipulate a Structured Tabluar File

Install the package with:

    pip install https://github.com/CivicKnowledge/metatab-py.git


Parsing Metatab Files
---------------------

The ``test-data`` directory has test files that also serve as examples to parse. 





Running a Metatab Server in Docker
----------------------------------

The ``docker`` directory contains Dockerfiles and Makefiles to operate them. The numbers ane redis containers are needed
only for production systems and the Google Spreadsheet plugin that generate ID numbers; you can safely ignore them.

To build and run the test metatab container:

    $ cd docker/metatab
    $ make build
    $ make start
    $ ./test.sh

