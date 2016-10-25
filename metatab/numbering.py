"""Server application for assigning dataset numbers. Requires a redis instance
for data storage.

Run with something like: python -m metatab.numbers  -p 80 -H 162.243.194.227


The access key is a secret key that the client will use to assign an assignment class.
The two classes are 'authority' and 'registered' Only central authority
operators ( like Clarinova ) should use the authoritative class. Other users can
use the 'registered' class. Without a key and class assignment, the callers us
the 'unregistered' class.

Set the key for the authority class with the redis-cli:

    set assignment_class:this-is-a-long-uid-key authoritative

For 'registered' users, use:

    set assignment_class:this-is-a-long-uid-key registered

There is only one uri to call:

    /next

It returns a JSON dict, with the 'number' key mapping to the number.

Running a redis server in docker
--------------------------------

Run the server, from https://hub.docker.com/_/redis/

    docker run --name ambry-redis -d redis redis-server --appendonly yes


Connect from a CLI:

    docker run -it --link ambry-redis:redis --rm redis sh -c 'exec redis-cli -h "$REDIS_PORT_6379_TCP_ADDR" -p "$REDIS_PORT_6379_TCP_PORT"'

Proxy
-----

You probably also want to run a web proxy, like Hipache:

    docker run --name hipache --link ambry-redis:redis -p 80:8080 -p 443:4430 hipache

Copyright (c) 2015 Civic Knowledge. This file is licensed under the terms of the
Revised BSD License, included in this distribution as LICENSE.txt

"""

from six import string_types
from bottle import error, hook, get, request, response  # , redirect, put, post
from bottle import HTTPResponse, install  # , static_file, url
from bottle import run  # , debug  # @UnresolvedImport
from decorator import decorator  # @UnresolvedImport
import logging
import string

logging.basicConfig(level=logging.DEBUG)

# Alternative number spaces, mostly for manifests and databases
# The main number space for datasets is 'd'
# Number spaces for Ambry are: d,p,t,c,F
NUMBER_SPACES = string.ascii_letters


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


class RedisPlugin(object):
    def __init__(self, pool, keyword='redis'):
        self.pool = pool
        self.keyword = keyword

    def setup(self, app):
        pass

    def apply(self, callback, context):
        import inspect
        import redis as rds

        # Override global configuration with route-specific values.
        conf = context['config'].get('redis') or {}

        keyword = conf.get('keyword', self.keyword)

        # Test if the original callback accepts a 'library' keyword.
        # Ignore it if it does not need a database handle.
        args = inspect.getargspec(context['callback'])[0]
        if keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            kwargs[keyword] = rds.Redis(connection_pool=self.pool)

            rv = callback(*args, **kwargs)

            return rv

        # Replace the route callback with the wrapped one.
        return wrapper


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


class Constant:
    """Organizes constants in a class."""

    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Can't rebind const(%s)" % name)
        self.__dict__[name] = value


class ObjectNumber(object):
    """Static class for holding constants and static methods related to object
    numbers.

    Note! Most of this code is stolen from ambry.identity, and is severly hacked. It's only
    good for generating numbers of the correct form.

    """

    # When a name is resolved to an ObjectNumber, orig can
    # be set to the input value, which can be important, for instance,
    # if the value's use depends on whether the user specified a version
    # number, since all values are resolved to versioned ONs
    orig = None
    assignment_class = 'self'

    TYPE = Constant()
    TYPE.DATASET = 'd'

    VERSION_SEP = ''

    DLEN = Constant()

    # Number of digits in each assignment class
    # TODO: Add a 22 digit version for UUIDs ( 2^128 ~= 62^22 )
    DLEN.DATASET = (3, 5, 7, 9)
    DLEN.DATASET_CLASSES = dict(
        authoritative=DLEN.DATASET[0],  # Datasets registered by number authority .
        registered=DLEN.DATASET[1],  # For registered users of a numbering authority
        unregistered=DLEN.DATASET[2],  # For unregistered users of a numebring authority
        self=DLEN.DATASET[3])  # Self registered

    # Because the dataset number can be 3, 5, 7 or 9 characters,
    # And the revision is optional, the datasets ( and thus all
    # other objects ) , can have several different lengths. We
    # Use these different lengths to determine what kinds of
    # fields to parse
    # 's'-> short dataset, 'l'->long dataset, 'r' -> has revision
    #
    # generate with:
    #     {
    #         ds_len+rl:(ds_len, (rl if rl != 0 else None), cls)
    #         for cls, ds_len in self.DLEN.ATASET_CLASSES.items()
    #         for rl in self.DLEN.REVISION
    #     }
    #
    DATASET_LENGTHS = {
        3: (3, None, 'authoritative'),
        5: (5, None, 'registered'),
        6: (3, 3, 'authoritative'),
        7: (7, None, 'unregistered'),
        8: (5, 3, 'registered'),
        9: (9, None, 'self'),
        10: (7, 3, 'unregistered'),
        12: (9, 3, 'self')}

    # Length of the caracters that aren't the dataset and revisions
    NDS_LENGTH = {'d': 0}

    @classmethod
    def base62_encode(cls, num):
        """Encode a number in Base X.

        `num`: The number to encode
        `alphabet`: The alphabet to use for encoding
        Stolen from: http://stackoverflow.com/a/1119769/1144479

        """

        alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

        if num == 0:
            return alphabet[0]
        arr = []
        base = len(alphabet)
        while num:
            rem = num % base
            num = num // base
            arr.append(alphabet[rem])
        arr.reverse()
        return ''.join(arr)

    @classmethod
    def _rev_str(cls, revision):

        if not revision:
            return ''

        revision = int(revision)
        return (
            ObjectNumber.base62_encode(revision).rjust(
                cls.DLEN.REVISION[1],
                '0') if bool(revision) else '')


class TopNumber(ObjectNumber):
    """A general top level number, with a given number space.

    Just like a DatasetNumber, with without the 'd'

    """

    def __init__(self, space, dataset=None, revision=None, assignment_class='self'):
        """Constructor."""

        if len(space) > 1:
            raise ValueError("Number space must be a single letter")

        self.space = space

        self.assignment_class = assignment_class

        self.dataset = dataset
        self.revision = revision

    def _ds_str(self):

        ds_len = self.DLEN.DATASET_CLASSES[self.assignment_class]

        return ObjectNumber.base62_encode(self.dataset).rjust(ds_len, '0')

    def __str__(self):
        return (self.space + self._ds_str() + ObjectNumber._rev_str(self.revision))


class DatasetNumber(ObjectNumber):
    """An identifier for a dataset."""

    def __init__(self, dataset=None, revision=None, assignment_class='self'):
        """Constructor."""
        import random

        self.assignment_class = assignment_class

        self.dataset = dataset
        self.revision = revision

    def _ds_str(self):
        ds_len = self.DLEN.DATASET_CLASSES[self.assignment_class]

        return ObjectNumber.base62_encode(self.dataset).rjust(ds_len, '0')

    def __str__(self):
        return (ObjectNumber.TYPE.DATASET + self._ds_str() + ObjectNumber._rev_str(self.revision))


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
def get_root(redis):
    return []


def request_delay(nxt, delay, delay_factor):
    """Calculate how long this client should be delayed before next request.

    :rtype : object

    """

    import time

    now = time.time()

    try:
        delay = float(delay)
    except (ValueError, TypeError):
        delay = 1.0

    nxt = float(nxt) if nxt else now - 1

    since = None
    if now <= nxt:
        # next is in the future, so the
        # request is rate limited

        ok = False

    else:
        # next is in the past, so the request can proceed
        since = now - nxt

        if since > 2 * delay:

            delay = int(delay / delay_factor)

            if delay < 1:
                delay = 1

        else:

            delay = int(delay * delay_factor)

        if nxt < now:
            nxt = now

        nxt = nxt + delay

        ok = True

    return ok, since, nxt, delay, nxt - now, (nxt + 4 * delay) - now


@get('/next')
@CaptureException
def get_next(redis, assignment_class=None, space=''):
    from time import time

    delay_factor = 2

    ip = str(request.remote_addr)
    now = time()

    next_key = "next:" + ip
    delay_key = "delay:" + ip

    if space and space in NUMBER_SPACES:
        spacestr = space + ':'
    else:
        spacestr = ''

    #
    # The assignment class determine how long the resulting number will be
    # which namespace the number is drawn from, and whether the user is rate limited
    # The assignment_class: key is assigned and set externally
    #
    access_key = request.query.access_key

    if access_key:
        assignment_class_key = "assignment_class:" + access_key
        assignment_class = (redis.get(assignment_class_key) or b'').decode('ascii')

    if not assignment_class:
        raise NotAuthorized('Use an access key to gain access to this service')

    #
    # These are the keys that store values, so they need to be augmented with the numebr space.
    # For backwards compatiility, the 'd' space is empty, but the other spaces have strings.
    #
    # The number space depends on the assignment class.
    number_key = "dataset_number:" + spacestr + assignment_class
    authallocated_key = "allocated:" + spacestr + assignment_class
    # Keep track of allocatiosn by IP
    ipallocated_key = "allocated:" + spacestr + ip

    nxt = redis.get(next_key)
    delay = redis.get(delay_key)

    # Adjust rate limiting based on assignment class
    if assignment_class == 'authoritative':
        since, nxt, delay, wait, safe = (0, now - 1, 0, 0, 0)

    elif assignment_class == 'registered':
        delay_factor = 1.1

    ok, since, nxt, delay, wait, safe = request_delay(nxt, delay, delay_factor)

    # with redis.pipeline() as pipe:
    with redis.pipeline():
        redis.set(next_key, nxt)
        redis.set(delay_key, delay)

    log_msg = 'ip={} ok={} since={} nxt={} delay={} wait={} safe={}' \
        .format(ip, ok, since, nxt, delay, wait, safe)

    logging.info(log_msg)

    if ok:
        number = redis.incr(number_key)

        if not space:
            dn = DatasetNumber(number, None, assignment_class)
        else:
            dn = TopNumber(space, number, None, assignment_class)

        redis.sadd(ipallocated_key, str(dn))
        redis.sadd(authallocated_key, str(dn))

    else:
        # More rate-limit punshment
        nxt = nxt + delay
        wait = nxt - now
        with redis.pipeline():
            redis.set(next_key, nxt)
            redis.set(delay_key, delay)

        raise TooManyRequests(' Access will resume in {} seconds'.format(wait))

    return dict(ok=ok,
                number=str(dn),
                assignment_class=assignment_class,
                wait=wait,
                safe_wait=safe,
                nxt=nxt,
                delay=delay)


@get('/next/<space>')
@CaptureException
def get_next_space(redis, assignment_class=None, space=''):
    if space not in NUMBER_SPACES:
        raise NotFound('Invalid number space: {}'.format(space))

    return get_next(redis, assignment_class=assignment_class, space=space)


@get('/find/<name>')
def get_find_term(name, redis):
    """Return an existing number for a bundle name, or return a new one."""

    nk = 'name:' + name

    # This code has a race condition. It can be fixed with pipe lines, but
    # that requires re-working get_next

    v = (redis.get(nk) or b'').decode('ascii')

    if v:
        d = dict(
            ok=True,
            number=v,
            assignment_class=None,
            wait=None,
            safe_wait=None,
            nxt=None,
            delay=0
        )

        return d

    else:
        d = get_next(redis)

        # get_next captures exceptions, so we'll have to deal with it as a
        # return value.
        if 'exception' not in d:
            redis.set(nk, d['number'])

        return d


@get('/echo/<term>')
def get_echo_term(term, redis):
    """Test function to see if the server is working."""
    # FIXME: Why twice? See previous function.

    return [term]


def _run(host, port, redis, unregistered_key, registered_key=None, authoritative_key=None,
         reloader=False, **kwargs):
    import redis as rds

    pool = rds.ConnectionPool(host=redis['host'], port=redis['port'], db=0)

    rds = rds.Redis(connection_pool=pool)

    # This is the key that can be distributed publically. It is only to
    # keep bots and spiders from sucking up a bunch of numbers.

    if unregistered_key:
        rds.set('assignment_class:' + unregistered_key, 'unregistered')
        logging.info("Setting unregistered key: {}".format(unregistered_key))

    if registered_key:
        rds.set('assignment_class:' + registered_key, 'registered')
        logging.info("Setting registered key: {}".format(registered_key))

    if authoritative_key:
        rds.set('assignment_class:' + authoritative_key, 'authoritative')
        logging.info("Setting authoritative key: {}".format(authoritative_key))

    install(RedisPlugin(pool))

    logging.info('Listening on {} {}'.format(host, port))

    return run(host=host, port=port, reloader=reloader, server='paste')


if __name__ == '__main__':
    import argparse
    import os
    from uuid import uuid4

    # Env vars set by docker when a link is made.
    docker_host = os.getenv('REDIS_PORT_6379_TCP_ADDR', 'localhost')
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

    parser.add_argument('-U', '--gen-unregistered-key', default=False, action='store_true',
                        help="Generate an unregistered keys")
    parser.add_argument('-G', '--gen-registered-key', default=False, action='store_true',
                        help="Generate a registered key")
    parser.add_argument('-A', '--gen-authoritative-key', default=False, action='store_true',
                        help="Generate an authoritative key")

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
