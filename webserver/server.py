import re
import traceback
from typing import List

import flask

import sys
sys.path.insert(0, '../')

import parser
from grammar.shared import specific, negation, claim, conditional, instance
from grammar import simple, recursive
from flask import Flask, render_template, request, jsonify
from collections import OrderedDict
import os
from interpretation import Interpretation
from argumentation import Argument, Relation


class TokenizeError(Exception):
    pass


class JSONEncoder(flask.json.JSONEncoder):
    def _simplify(self, o, context):
        if isinstance(o, Argument):
            print(repr(o.instances))
            return dict(
                claims=[self._simplify(claim, context) for claim in o.claims],
                relations=[self._simplify(relation, context) for relation in o.relations],
                instances=[
                    dict(
                        cls='instance',
                        id=instance.id,
                        name=instance.name,
                        noun=instance.noun,
                        pronoun=instance.pronoun,
                        repr=repr(instance),
                        occurrences=[
                            dict(
                                cls='instance',
                                id=other_occurrence.id,
                                name=other_occurrence.name,
                                noun=other_occurrence.noun,
                                pronoun=other_occurrence.pronoun,
                                repr=repr(other_occurrence)
                            ) for other_occurrence in other_occurrences
                        ]
                    ) for instance, other_occurrences in o.instances.items()
                ]
            )
        elif isinstance(o, claim.Claim):
            op = context.find_claim(o)
            return dict(cls='claim', id=op.id, text=op.text(context), assumption=op.assumption)
        elif isinstance(o, Relation):
            return dict(cls='relation', id=hash(o),
                sources=[dict(cls='claim', id=context.find_claim(claim).id) for claim in o.sources],
                target=self._simplify(o.target, context),
                type=o.type)
        else:
            raise TypeError('Cannot _simplify ' + type().__name__)
        
    def default(self, o):
        if isinstance(o, Interpretation):
            return self._simplify(o.argument, o.argument)
        # elif '__dict__' in dir(o):
        #     return o.__dict__
        # elif isinstance(o, set):
        #     return list(o)
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


# grammar = general.grammar \
#     | specific.grammar \
#     | negation.grammar \
#     | simple.grammar

# # Print grammar to terminal for assurance that we're not mad
# print("Grammar:")
# for rule in sorted(grammar, key=lambda rule: rule.name):
#     print("  " + str(rule))
# print()

grammars = {
    'simple':specific.grammar | conditional.grammar | negation.grammar | simple.grammar,
    'recursive':specific.grammar | conditional.grammar | negation.grammar | recursive.grammar
}


@app.route('/')
def hello():
    return render_template('index.html', sections=sentences)


@app.route('/api/parse', methods=['GET'])
def api_parse_sentence():
    grammar_name = request.args.get('grammar', 'simple')
    tokens = parser.tokenize(request.args.get('sentence'))
    reply = dict(tokens=tokens, grammar=grammar_name)

    try:
        try:
            grammar = grammars[grammar_name]
        except:
            raise Exception('Grammar {} not available'.format(grammar_name));

        p = parser.Parser(grammar, 'ARGUMENT')
        parses = p.parse(tokens)
        reply['parses'] = parses
        return jsonify(reply)
    except Exception as error:
        traceback.print_exc()
        reply['error'] = str(error)
        response = jsonify(reply)
        response.status_code = 400
        return response


if __name__ == '__main__':
    app.run(extra_files=sentence_files)