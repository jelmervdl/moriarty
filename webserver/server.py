import re
from typing import List

import flask

import parser
import grammar
from flask import Flask, render_template, request, jsonify

class TokenizeError(Exception):
    pass


class JSONEncoder(flask.json.JSONEncoder):
    def default(self, o):
        if isinstance(o, grammar.Operation):
            return o.as_tuple()
        else:
            return super().default(o)


app = Flask(__name__)
app.secret_key = 'Tralalala'
app.json_encoder = JSONEncoder
app.debug = True


def tokenize(sentence: str) -> List[str]:
    return re.compile('\w+|\$[\d\.]+|\S+').findall(sentence)


@app.errorhandler(parser.ParseError)
def handle_parse_error(error: parser.ParseError):
    reply = dict(error=str(error))
    if request.method == 'POST' and 'sentence' in request.form:
        reply['tokens'] = tokenize(request.form['sentence'])
    response = jsonify(reply)
    response.status_code = 400
    return response


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/api/parse', methods=['POST'])
def api_parse_sentence():
    tokens = tokenize(request.form['sentence'])

    p = parser.Parser(grammar.rules, grammar.start)
    parses = p.parse(tokens)

    reply = dict(tokens=tokens, parses=parses)

    return jsonify(reply)


if __name__ == '__main__':
    app.run()