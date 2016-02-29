import re
from typing import List

import flask

import sys
sys.path.insert(0, '../')

import parser
import grammar2 as grammar
from flask import Flask, render_template, request, jsonify

class TokenizeError(Exception):
    pass


class JSONEncoder(flask.json.JSONEncoder):
    def default(self, o):
        if 'as_tuple' in dir(o):
            return o.as_tuple()
        else:
            return super().default(o)


app = Flask(__name__)
app.secret_key = 'Tralalala'
app.json_encoder = JSONEncoder
app.debug = True


@app.errorhandler(parser.ParseError)
def handle_parse_error(error: parser.ParseError):
    reply = dict(error=str(error))
    if 'sentence' in request.args:
        reply['tokens'] = tokenize(request.args['sentence'])
    response = jsonify(reply)
    response.status_code = 400
    return response


@app.route('/')
def hello():
    return render_template('index.html', sentences=grammar.sentences)


@app.route('/api/parse', methods=['GET'])
def api_parse_sentence():
    tokens = parser.tokenize(request.args.get('sentence'))

    p = parser.Parser(grammar.rules, grammar.start)
    parses = p.parse(tokens)

    reply = dict(tokens=tokens, parses=parses)

    return jsonify(reply)


if __name__ == '__main__':
    app.run()