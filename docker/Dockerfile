
FROM python:3.6.1-alpine

MAINTAINER Eric Busboom "eric@civicknowledge.com"

VOLUME /opt/metatab

RUN apk add --update --no-cache g++ gcc libxslt-dev==1.1.29-r0 bash

RUN pip install https://github.com/CivicKnowledge/metatab-py/archive/master.zip # 1
