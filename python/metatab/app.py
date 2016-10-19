""" Flask application to parse STF Files
"""

from six import string_types
from bottle import error, hook, get, request, response  # , redirect, put, post
from bottle import HTTPResponse, install  # , static_file, url
from bottle import run  # , debug  # @UnresolvedImport
from decorator import decorator  # @UnresolvedImport
import logging
import string

logging.basicConfig(level=logging.DEBUG)


class NotFound(Exception):
    pass


class InternalError(Exception):
    pass


class NotAuthorized(Exception):
    pass


class TooManyRequests(Exception):
    pass


def capture_return_exception(e):
    import sys
    import traceback

    # (exc_type, exc_value, exc_traceback) = sys.exc_info()  # @UnusedVariable

    tb_list = traceback.format_list(traceback.extract_tb(sys.exc_info()[2]))

    return {'exception': {
        'class': e.__class__.__name__,
        'args': e.args,
        'trace': "\n".join(tb_list)
    }}



def _CaptureException(f, *args, **kwargs):
    """Decorator implementation for capturing exceptions."""

    try:
        r = f(*args, **kwargs)
    except HTTPResponse:
        raise  # redirect() uses exceptions
    except Exception as e:
        r = capture_return_exception(e)
        if hasattr(e, 'code'):
            response.status = e.code

    return r


def CaptureException(f, *args, **kwargs):
    """Decorator to capture exceptions and convert them to a dict that can be
    returned as JSON."""

    return decorator(_CaptureException, f)  # Preserves signature


class AllJSONPlugin(object):
    """A copy of the bottle JSONPlugin, but this one tries to convert all
    objects to json."""

    from json import dumps as json_dumps

    name = 'json'
    remote = 2

    def __init__(self, json_dumps=json_dumps):
        self.json_dumps = json_dumps

    def apply(self, callback, context):

        dumps = self.json_dumps
        if not dumps:
            return callback

        def wrapper(*a, **ka):
            rv = callback(*a, **ka)

            if isinstance(rv, HTTPResponse):
                return rv

            if isinstance(rv, string_types):
                return rv

            # Attempt to serialize, raises exception on failure
            try:
                json_response = dumps(rv)
            except Exception as e:
                r = capture_return_exception(e)
                json_response = dumps(r)

            # Set content type only if serialization succesful
            response.content_type = 'application/json'
            return json_response

        return wrapper


install(AllJSONPlugin())



@error(404)
@CaptureException
def error404(error):
    raise NotFound("For url: {}".format(repr(request.url)))


@error(500)
def error500(error):
    raise InternalError("For Url: {}".format(repr(request.url)))


@hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'


@get('/')
def get_root():
    return ['Nothing Here']


def _run(host, port, reloader=False, **kwargs):


    logging.info('Listening on {} {}'.format(host, port))

    return run(host=host, port=port, reloader=reloader, server='paste')


if __name__ == '__main__':
    import argparse
    import os
    from uuid import uuid4

    # Env vars set by docker when a link is made.
    docker_host = os.getenv('REDIS_PORT_6379_TCP_ADDR')
    docker_port = os.getenv('REDIS_PORT_6379_TCP_PORT', 6379)

    unregistered_key = os.getenv('UNREGISTERED_KEY', None)
    registered_key = os.getenv('REGISTERED_KEY', None)
    authoritative_key = os.getenv('AUTHORITATIVE_KEY', None)

    numbers_host = os.getenv('NUMBERS_HOST', '0.0.0.0')

    d = {
        'reloader': False,
        'host': numbers_host,
        'port': 80,
        'redis': {
            'host': docker_host,
            'port': docker_port

        },
        'unregistered_key': unregistered_key,
        'registered_key': registered_key,
        'authoritative_key': authoritative_key,
    }

    parser = argparse.ArgumentParser(prog='python -mambry.server.numbers',
                                     description='Run an Ambry numbers server')

    parser.add_argument('-H', '--server-host', default=None, help="Server host. ")

    parser.add_argument('-p', '--server-port', default=None, help="Server port.")
    parser.add_argument('-R', '--redis-host', default=docker_host, help="Redis host.")
    parser.add_argument('-r', '--redis-port', default=docker_port, help="Redis port.")
    parser.add_argument('-d', '--debug', default=False, action='store_true')
    parser.add_argument('-u', '--unregistered-key', default=None, help="access_key value for unregistered access")
    parser.add_argument('-g', '--registered-key', default=None, help="access_key value for registered access")
    parser.add_argument('-a', '--authoritative-key', default=None, help="access_key value for authoritative access")

    parser.add_argument('-U', '--gen-unregistered-key', default=False, action='store_true', help="Generate an unregistered keys")
    parser.add_argument('-G', '--gen-registered-key', default=False, action='store_true', help="Generate a registered key")
    parser.add_argument('-A', '--gen-authoritative-key', default=False, action='store_true', help="Generate an authoritative key")

    args = parser.parse_args()

    if args.server_port:
        d['port'] = args.server_port

    if args.server_host:
        d['host'] = args.server_host

    if args.redis_port:
        d['redis']['port'] = args.redis_port

    if args.redis_host:
        d['redis']['host'] = args.redis_host

    if args.unregistered_key:
        d['unregistered_key'] = args.unregistered_key
    elif args.gen_unregistered_key:
        d['unregistered_key'] = str(uuid4())

    if args.registered_key:
        d['registered_key'] = args.registered_key
    elif args.gen_registered_key:
        d['registered_key'] = str(uuid4())

    if args.authoritative_key:
        d['authoritative_key'] = args.authoritative_key
    elif args.gen_authoritative_key:
        d['authoritative_key'] = str(uuid4())

    if args.debug:
        d['reloader'] = args.debug

    _run(**d)

