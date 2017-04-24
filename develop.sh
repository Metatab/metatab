#!/bin/bash 
git clone https://github.com/CivicKnowledge/rowpipe.git && (cd rowpipe && python setup.py develop)
git clone https://github.com/CivicKnowledge/tableintuit.git && (cd tableintuit && python setup.py develop)
git clone https://github.com/CivicKnowledge/rowgenerators.git && (cd rowgenerators && python setup.py develop)
git clone https://github.com/CivicKnowledge/pandas-reporter.git && (cd pandas-reporter && python setup.py develop)
git clone https://github.com/CivicKnowledge/metatab-py.git; (cd metatab-py && python setup.py develop)
