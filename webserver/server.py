import re
from typing import List

import flask

import sys
sys.path.insert(0, '../')

import parser
from grammar.shared import general, specific, negation, claim
from grammar import simple
from flask import Flask, render_template, request, jsonify
from collections import OrderedDict
import os
from interpretation import Interpretation
from argumentation import Argument, Relation

class TokenizeError(Exception):
    pass


class JSONEncoder(flask.json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Interpretation):
            return o.argument
        elif isinstance(o, Argument):
            return o.__dict__
        elif isinstance(o, claim.Claim):
            return dict(cls='claim', id=hash(o), text=str(o))
        elif isinstance(o, Relation):
            return dict(cls='relation', id=hash(o), sources=o.sources, target=o.target, type=o.type)
        elif '__dict__' in dir(o):
            return o.__dict__
        elif isinstance(o, set):
            return list(o)
        else:
            return super().default(o)


app = Flask(__name__)
app.secret_key = 'Tralalala'
app.json_encoder = JSONEncoder
app.debug = True

# Load sentence files
sentence_files = [os.path.join(os.path.dirname(__file__), '../sentences.txt')]
sentences = OrderedDict()

for sentence_file in sentence_files:
    with open(sentence_file, 'r') as fh:
        sentences.update(parser.read_sentences(fh))


grammar = general.grammar \
    | specific.grammar \
    | negation.grammar \
    | simple.grammar

# Print grammar to terminal for assurance that we're not mad
print("Grammar:")
for rule in sorted(grammar, key=lambda rule: rule.name):
    print("  " + str(rule))
print()

@app.errorhandler(parser.ParseError)
def handle_parse_error(error: parser.ParseError):
    reply = dict(error=str(error))
    if 'sentence' in request.args:
        reply['tokens'] = parser.tokenize(request.args['sentence'])
    response = jsonify(reply)
    response.status_code = 400
    return response


@app.route('/')
def hello():
    return render_template('index.html', sections=sentences)


@app.route('/api/parse', methods=['GET'])
def api_parse_sentence():
    tokens = parser.tokenize(request.args.get('sentence'))

    p = parser.Parser(grammar, 'ARGUMENT')
    parses = p.parse(tokens)

    reply = dict(tokens=tokens, parses=parses)

    return jsonify(reply)


if __name__ == '__main__':
    app.run(extra_files=sentence_files)