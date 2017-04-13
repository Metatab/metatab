
FROM python:3.6.1-alpine

MAINTAINER Eric Busboom "eric@civicknowledge.com"

VOLUME /opt/metatab

RUN apk add --update --no-cache g++ gcc python-dev py-lxml libxslt-dev==1.1.29-r0 bash git

RUN pip install https://github.com/CivicKnowledge/metatab-py/archive/master.zip # 9
