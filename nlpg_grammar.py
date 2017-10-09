from typing import NamedTuple, List, Optional, Any
from nlpg import ruleset, rule, tlist, template, l, slot, empty, terminal, NoMatchException
import re

class Text(object):
	def __init__(self, words):
		self.words = words

	def __str__(self):
		return " ".join(self.words)

	def __repr__(self):
		return "Text('{}')".format(str(self))


class Claim(NamedTuple):
	text: Text


class Argument(NamedTuple):
	claim: Claim
	supports: List['Support']


class Support(NamedTuple):
	datums: List[Claim]
	warrant: Optional[Argument]
	undercutter: Optional[Argument]


class Warrant(NamedTuple):
	claim: Claim
	conditions: List['WarrantCondition'] # in Disjunctive Normal Form
	exceptions: List['WarrantException'] # idem.

class WarrantCondition(NamedTuple):
	claims: List[Claim] # Conjunctive

class WarrantException(NamedTuple):
	claims: List[Claim] # Conjunctive

class Word(terminal):
	def test(self, word):
		return isinstance(word, Text)

	def consume(self, word):
		return word

	def reverse(self, word):
		if not isinstance(word, Text):
			raise NoMatchException('Word not a unit')
		return word

def and_rule(name, single, cc=l('and')):
	comma = name + '_'
	return [
		rule(name, [single], tlist(head=slot(0))),
		rule(name, [single, cc, single], tlist(head=[slot(0),slot(2)])),
		rule(name, [comma], slot(0)),
		rule(comma, [single, l(','), comma], tlist(head=slot(0), tail=slot(2))),
		rule(comma, [single, l(','), single, l(','), cc, single], tlist(head=[slot(0), slot(2), slot(5)])),
	]

rules = ruleset([
	rule('sentences',
		['sentence', 'sentences'],
		tlist(head=slot(0), tail=slot(1))),

	rule('sentences',
		['sentence'],
		tlist(head=slot(0))),

	rule('sentence',
		['argument', l('.')],
		slot(0)),

	rule('sentence',
		['warrant', l('.')],
		slot(0)),
	
	] + and_rule('arguments', 'argument') + [
	
	rule('argument',
		['claim', 'supports?'],
		template(Argument, claim=slot(0), supports=slot(1))),

	rule('claim',
		['word'],
		template(Claim, text=slot(0))),

	] + and_rule('claims', 'claim') + [
	
	rule('word',
		[Word()],
		slot(0)),

	rule('supports?',
		[],
		tlist()),
	rule('supports?',
		['supports'],
		slot(0)),

	] + and_rule('supports', 'support') + [
	
	rule('support',
		[l('because'), 'arguments', 'warrant?', 'undercutter?'],
		template(Support, datums=slot(1), warrant=slot(2), undercutter=slot(3))),

	rule('undercutter?',
		[],
		empty()),
	rule('undercutter?',
		[l('except'), 'argument'],
		slot(1)),

	rule('warrant?',
		[],
		empty()),
	rule('warrant?',
		[l('and'), 'warrant'],
		slot(1)),

	rule('warrant',
		['claim', 'conditions?', 'exceptions?'],
		template(Warrant, claim=slot(0), conditions=slot(1), exceptions=slot(2))),

	rule('conditions?',
		[],
		tlist()),
	rule('conditions?',
		[l('if'), 'conditions'],
		slot(1)),
	rule('conditions?',
		[l('when'), 'conditions'],
		slot(1)),

	] + and_rule('conditions', 'condition', l('or')) + [
	
	rule('condition',
		['claims'],
		template(WarrantCondition, claims=slot(0))),

	rule('exceptions?',
		[],
		tlist()),
	rule('exceptions?',
		[l('unless'), 'exceptions'],
		slot(1)),
	rule('exceptions?',
		[l('except'), l('when'), 'exceptions'],
		slot(2)),

	] + and_rule('exceptions', 'exception', l('or')) + [
	
	rule('exception',
		['claims'],
		template(WarrantException, claims=slot(0))),
])


def tokenize(markers, sentence):
	unit = []
	for token in re.findall(r"[\w'/]+|[.,!?;]", sentence):
		if token in markers:
			if len(unit) > 0:
				yield Text(unit)
				unit = []
			yield token
		else:
			unit.append(token)
	if len(unit) > 0:
		yield Text(unit)


if __name__ == '__main__':
	from nlpg import Parser
	from nlpg_lc import LCParser
	from pprint import pprint
	from sys import exit

	assert len(rules.missing()) == 0, "Missing rules for {!r}".format(rules.missing())

	print("Unreachable", end=": ")
	pprint(rules.unreachable())

	print("Markers", end=": ")
	pprint(rules.markers())

	parser = Parser(rules)

	class Test(object):
		def __init__(self, start, sentence, expected = None):
			self.start = start
			self.sentence = sentence
			self.expected = expected

		def test(self, runner):
			out = runner(self.sentence, start=self.start)
			if self.expected and out != self.expected:
				print("Expected ", end='')
				pprint(self.expected)

	def parse(sentence, start='sentence'):
		tokens = list(tokenize(rules.markers(), sentence))
		parse = parser.parse(start, tokens)
		parses = []
		print(tokens)
		for n, tree in enumerate(parse):
			print(n, end=': ')
			pprint(tree)
			parses.append(tree)

			for realisation in parser.reverse(start, tree):
				print(" ".join(map(str, realisation)))

		if hasattr(parse, 'counter'):
			print("Evaluated {} paths".format(parse.counter))
		return parses

	parse('Tweety can fly because Tweety is a bird and animals can fly when they have wings unless they are a penguin .')
	parse('The act is unlawful when someone\'s right is violated except when there is a justification .')
	parse('The act is unlawful because someone\'s right was violated except there is a justification .')
	parse('A suspect is innocent unless they are found guilty .')
	parse('Claim A because claim B, claim C, and claim D.')

