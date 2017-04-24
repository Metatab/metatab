Loading Census Data With Pandas Reporter
========================================

The general process for creating a census package is similar to the package process described in the `Getting Started tutorial, <https://github.com/CivicKnowledge/metatab-py/blob/master/docs/GettingStarted.rst>`_ but with a ``DataFile`` term that uses a program to fetch data from Census Reporter. First we'll create the program, then link it into a Metatab package. The program uses the `pandas-reporter` module, so the reation process is very similar to the `Pandas-Reporter tutorial. <https://github.com/CivicKnowledge/pandas-reporter/blob/master/test/Pandas%20Reporter%20Examples.ipynb>`_

Creating a Pandas-Reporter program
----------------------------------

First, read the `Pandas-Reporter tutorial. <https://github.com/CivicKnowledge/pandas-reporter/blob/master/test/Pandas%20Reporter%20Examples.ipynb>`_ You'l need to install the `pandasreporter` python module.

Then, visit `Census Reporter <http://censusreporter.org>`_ to locate information about tables, regions and  and summary levels.

For this tutorial, we will use these tables:

- B17001, Poverty Status by Sex by Age
- B17024, Age by Ratio of Income to Poverty Level
- B17017, Poverty Status by Household Type by Age of Householder

For the geography, we will use tracts in San Diego County.

To find the geoid code for San Diego County, visit the main page at `Census Reporter <http://censusreporter.org>`_ and search for San Diego County. You should get a `profile page for the county <https://censusreporter.org/profiles/05000US06073-san-diego-county-ca/> '_. In the URL for the page, you should see the code `05000US06073`. This code is the geoid for San Diego County.

Next, visit the page for `Cartographic Boundary File Summary Level Codes <https://www.census.gov/geo/maps-data/data/summary_level.html>`_ to get the summary level code for tracts. It is actually listed by all of its components, in this case, 	"State-County-Census Tract." It is code "140". ( BTW, that is a string, not a number. )

The start of our program is similar to the program in the `Pandas-Reporter tutorial. <https://github.com/CivicKnowledge/pandas-reporter/blob/master/test/Pandas%20Reporter%20Examples.ipynb>`_, except using the table, summary level and region codes for this example:

.. code-block:: python

    $ mkdir example-data-package
    $ cd example-data-package
    $ metapack -c