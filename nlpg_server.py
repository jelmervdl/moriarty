from flask import Flask, render_template_string, request, jsonify, send_from_directory

from nlpg import Parser, \
	ruleset, rule, l, \
	empty, tlist, template, select, \
	claim, argument, relation, diagram

from pprint import pprint

rules = ruleset([
	rule('extended_claims',
		['extended_claim'],
		tlist(0)),
	rule('extended_claims',
		['extended_claim', l('and'), 'extended_claims'],
		tlist(0, 2)),
	rule('extended_claim',
		['claim', 'supports', 'attacks'],
		template(argument, claim=0, supports=1, attacks=2)),
	rule('claim',
		[l('birds'), l('can'), l('fly')],
		template(claim, id='b_can_f')),
	rule('claim',
		[l('Tweety'), l('can'), l('fly')],
		template(claim, id='t_can_f')),
	rule('claim',
		[l('Tweety'), l('has'), l('wings')],
		template(claim, id='t_has_w')),
	rule('claim',
		[l('Tweety'), l('is'), l('a'), l('bird')],
		template(claim, id='t_is_b')),
	rule('claim',
		[l('Tweety'), l('is'), l('a'), l('penguin')],
		template(claim, id='t_is_p')),
	rule('claim',
		[l('Tweety'), l('is'), l('awesome')],
		template(claim, id='t_is_a')),
	rule('supports',
		[],
		tlist()),
	rule('supports',
		['support'],
		tlist(0)),
	rule('supports',
		['support', l('and'), 'supports'],
		tlist(0, 2)),
	rule('support',
		[l('because'), 'extended_claims'],
		select(1)),
	rule('attacks',
		[],
		tlist()),
	rule('attacks',
		['attack'],
		tlist(0)),
	rule('attacks',
		['attack', l('and'), 'attacks'],
		tlist(0, 2)),
	rule('attack',
		[l('but'), 'extended_claims'],
		select(1))
])

parser = Parser(rules)
parser.root = 'extended_claim'


def claim_to_json(c):
	assert isinstance(c, claim)
	return {
		'isa': 'claim',
		'id': c.id
	}


def relation_to_json(r):
	assert isinstance(r, relation)
	return {
		'isa': 'relation',
		'type': r.type,
		'sources': [claim_to_json(source) for source in r.sources],
		'target': claim_to_json(r.target)
	}


def diagram_to_json(diag):
	assert isinstance(diag, diagram)
	return {
		'isa': 'diagram',
		'claims': [claim_to_json(c) for c in diag.claims],
		'relations': [relation_to_json(c) for c in diag.relations]
	}


def json_to_diagram(json):
	return diagram(
		claims=frozenset(
			claim(id=c['id'])
			for c in json['claims']
		),
		relations=frozenset(
			relation(
				sources=frozenset(
					claim(id=c['id'])
					for c in r['sources']
				),
				target=claim(id=r['target']['id']),
				type=r['type']
			)
			for r in json['relations']
		)
	)


def text_to_diagrams(text):
	for tree in parser.parse(parser.root, text):
		yield diagram.from_tree(tree)


def diagram_to_texts(diagram):
	# This is because a tree has a top argument, but a diagram does not. So it
	# can be the case that an argument contains multiple trees.
	for tree in diagram.as_trees():
		for realisation in parser.reverse(parser.root, tree):
			yield realisation


app = Flask(__name__, static_folder='webserver/static')
app.secret_key = 'notrelevant'
app.debug = True

@app.route('/')
def app_index():
	with open('nlpg.html') as template:
		return render_template_string(template.read())

@app.route('/api/diagram', methods=['POST'])
def app_text_to_diagram():
	diagrams = list(diagram_to_json(diag) for diag in text_to_diagrams(request.json['text']))
	return jsonify(diagrams=diagrams)

@app.route('/api/text', methods=['POST'])
def app_diagram_to_text():
	diag = json_to_diagram(request.json['diagram'])
	pprint(diag)
	return jsonify(texts=list(diagram_to_texts(diag)))

if __name__ == '__main__':
	app.run()