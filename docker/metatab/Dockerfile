#
# Ambry Numbers Server
#
# Run this container with a link to a redis container, via the name 'ambry-redis'
FROM jfloff/alpine-python:2.7

MAINTAINER Eric Busboom "eric@civicknowledge.com"

VOLUME /opt/metatab

COPY requirements.txt /opt/metatab/requirements.txt

RUN pip install -r /opt/metatab/requirements.txt # v5

EXPOSE 80

CMD gunicorn -w 4 --max-requests 10 --timeout 300 --access-logfile - --error-logfile - \
-b 0.0.0.0:80 metatab.server:app