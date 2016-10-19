#
# Ambry Numbers Server
#
# Run this container with a link to a redis container, via the name 'ambry-redis'
FROM jfloff/alpine-python:3.4

MAINTAINER Eric Busboom "eric@civicknowledge.com"

VOLUME /data

COPY requirements /tmp
RUN pip install -r /tmp/requirements.txt

RUN pip install git+https://github.com/CivicKnowledge/metatab.git

EXPOSE 80

CMD python -metatab.numbering -UGA