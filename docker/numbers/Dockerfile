#
# Ambry Numbers Server
#
# Run this container with a link to a redis container, via the name 'ambry-redis'
FROM jfloff/alpine-python:3.4

MAINTAINER Eric Busboom "eric@civicknowledge.com"

VOLUME /data

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

RUN pip install git+https://github.com/CivicKnowledge/metatab-py.git # 1

EXPOSE 80

CMD python -mmetatab.numbering -UGA