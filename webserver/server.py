import re
import traceback
from typing import List
from functools import reduce

import flask

import sys
sys.path.insert(0, '../')

import parser
from grammar.shared import specific, negation, claim, conditional, instance
from grammar import simple, recursive, blob
from flask import Flask, render_template, request, jsonify
from collections import OrderedDict
import os
from interpretation import Interpretation
from argumentation import Argument, Relation


def ucfirst(string):
    '''Make the first letter of a string uppercase.
    
    Like PHP's ucfirst, this only affects the first character of a string.
    Because str.title capitalises every word, and str.capitalize lowers all
    other words.
    '''
    return string[0].upper() + string[1:]


class TokenizeError(Exception):
    pass


class JSONEncoder(flask.json.JSONEncoder):
    def _simplify(self, o, context):
        if isinstance(o, Argument):
            condition_claims = set()
            argument_claims = set()
            for relation in o.relations:
                if relation.type == Relation.CONDITION:
                    condition_claims.update(relation.sources)
                else:
                    argument_claims.update(relation.sources)

            excluded_claims = condition_claims - argument_claims

            return dict(
                claims=[self._simplify(claim, context) for claim in o.claims if claim not in excluded_claims],
                relations=[self._simplify(relation, context) for relation in o.relations if relation.type != Relation.CONDITION],
                instances=[
                    dict(
                        cls='instance',
                        id=instance.id,
                        # name=str(instance.name),
                        noun=str(instance.noun),
                        pronoun=str(instance.pronoun),
                        repr=repr(instance),
                        occurrences=[
                            dict(
                                cls='instance',
                                id=other_occurrence.id,
                                # name=str(other_occurrence.name),
                                noun=str(other_occurrence.noun),
                                pronoun=str(other_occurrence.pronoun),
                                repr=repr(other_occurrence)
                            ) for other_occurrence in other_occurrences
                        ]
                    ) for instance, other_occurrences in o.instances.items()
                ]
            )
        elif isinstance(o, claim.Claim):
            op = context.find_claim(o)
            return dict(cls='claim', id=op.id,
                text=ucfirst(op.text(context)),
                assumption=op.assumption,
                scope=self._simplify(op.scope, context))
        elif isinstance(o, Relation):
            def unique_claims(simplified_claims, claim):
                claim_id = context.find_claim(claim).id
                for simplified_claim in simplified_claims:
                    if simplified_claim['id'] == claim_id:
                        return simplified_claims
                simplified_claims.append(dict(cls='claim', id=claim_id))
                return simplified_claims

            return dict(cls='relation', id=id(o),
                sources=reduce(unique_claims, o.sources, []),
                target=self._simplify(o.target, context),
                assumption=o.assumption,
                type=o.type)
        elif isinstance(o, claim.Scope):
            return o.id
        elif o is None:
            return o
        else:
            raise TypeError('Cannot _simplify ' + type(o).__name__)
    
    def default(self, o):
        if isinstance(o, Interpretation):
            return self._simplify(o.argument, o.argument)
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
    'simple': specific.grammar | conditional.grammar | negation.grammar | simple.grammar,
    'recursive': specific.grammar | conditional.grammar | negation.grammar | recursive.grammar,
    'recursive_fallback': specific.grammar | conditional.grammar | negation.grammar | blob.grammar,
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
        # reply['states'] = p.table
        return jsonify(reply)
    except Exception as error:
        traceback.print_exc()
        reply['error'] = "{}: {!s}\n{}".format(error.__class__.__name__, error, traceback.format_exc())
        response = jsonify(reply)
        response.status_code = 400
        return response


if __name__ == '__main__':
    app.run(extra_files=sentence_files)