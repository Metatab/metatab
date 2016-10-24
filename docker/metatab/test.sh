#!/bin/bash

PORT=$(docker port metatab|awk -F: '{print $2}')
curl -H "Content-Type: text/csv" --data-binary '@../../test-data/children.csv' http://localhost:$PORT/v1/parse

