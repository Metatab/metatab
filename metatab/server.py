""" A Flask Application for Parsing files

Send a CSV file:

    curl -H "Content-Type: text/csv" --data-binary '@../test/data/example1-web.csv' http://127.0.0.1:5000/v1/parse

Also accepts a JSON list of rows.

"""
from flask import Flask, request, jsonify
from metatab.parser import TermGenerator, TermParser
from metatab.generate import RowGenerator, CsvDataRowGenerator

app = Flask(__name__)


class ClientError(Exception):
    status_code = 400

    messages = {
        400: 'Bad Request',
        415: 'Unsupported media type'
    }

    def __init__(self, status_code, message=None, payload=None):

        try:
            self.message = self.messages[status_code]
        except KeyError as e:
            self.message = ''

        if message:
            self.message += ': ' + message

        Exception.__init__(self, self.message)

        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())

        return dict(
            result=None,
            errors=[
                dict(
                    error=self.message
                )
            ]
        )


@app.errorhandler(ClientError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/')
def home():
    return 'metatab'


@app.route('/v1/parse', methods=['POST'])
def parse():
    content_type = request.headers.get('content-type')

    if content_type == 'application/json':
        rg = RowGenerator(request.json)
    elif content_type == 'text/csv':
        rg = CsvDataRowGenerator(request.data)
    else:
        raise ClientError(415, 'Bad mime type: {}'.format(content_type))

    term_gen = list(TermGenerator(rg))
    term_interp = TermParser(term_gen)

    d = term_interp.as_dict()

    return jsonify(dict(result=d, errors=term_interp.errors_as_dict()))


if __name__ == '__main__':
    app.run()
