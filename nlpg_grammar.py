from typing import NamedTuple, List, Optional, Any
from nlpg import ruleset, rule, tlist, template, l, select, empty, terminal, NoMatchException


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
	rebuttal: Optional[Argument]


class Warrant(NamedTuple):
	claim: Claim
	conditions: List['WarrantCondition']
	exceptions: List['WarrantException']

class WarrantCondition(NamedTuple):
	claims: List[Claim]

class WarrantException(NamedTuple):
	claims: List[Claim]

class Word(terminal):
	def test(self, word):
		return isinstance(word, Text)

	def consume(self, word):
		return word

	def reverse(self, word):
		if not isinstance(word, Text):
			raise NoMatchException('Word not a unit')
		return word


rules = ruleset([
	rule('sentence',
		['argument', l('.')],
		select(0)),

	rule('sentence',
		['warrant', l('.')],
		select(0)),

	rule('arguments',
		['argument'],
		tlist(head=0)),
	rule('arguments',
		['argument', l('and'), 'arguments'],
		tlist(head=0, rest=2)),

	rule('argument',
		['claim', 'supports?'],
		template(Argument, claim=0, supports=1)),

	rule('claim',
		['word'],
		template(Claim, text=0)),

	rule('claims',
		['claim'],
		tlist(head=0)),
	rule('claims',
		['claim', l('and'), 'claims'],
		tlist(head=0, rest=2)),

	rule('word',
		[Word()],
		select(0)),

	rule('supports?',
		[],
		tlist()),
	rule('supports?',
		['supports'],
		select(0)),

	rule('supports',
		['support'],
		tlist(head=0)),
	rule('supports',
		['support', l('and'), 'supports'],
		tlist(head=0, rest=2)),

	rule('support',
		[l('because'), 'arguments', 'warrant?', 'rebuttal?'],
		template(Support, datums=1, warrant=2, rebuttal=3)),

	rule('rebuttal?',
		[],
		empty()),
	rule('rebuttal?',
		[l('except'), 'argument'],
		select(1)),

	rule('warrant?',
		[],
		empty()),
	rule('warrant?',
		[l('and'), 'warrant'],
		select(1)),

	rule('warrant',
		['claim', 'conditions?', 'exceptions?'],
		template(Warrant, claim=0, conditions=1, exceptions=2)),

	rule('conditions?',
		[],
		tlist()),
	rule('conditions?',
		[l('if'), 'conditions'],
		select(1)),
	rule('conditions?',
		[l('when'), 'conditions'],
		select(1)),

	rule('conditions',
		['condition'],
		tlist(head=0)),
	rule('conditions',
		['condition', l('or'), 'conditions'],
		tlist(head=0, rest=2)),

	rule('condition',
		['claims'],
		template(WarrantCondition, claims=0)),

	rule('exceptions?',
		[],
		tlist()),
	rule('exceptions?',
		[l('unless'), 'exceptions'],
		select(1)),
	rule('exceptions?',
		[l('except'), l('when'), 'exceptions'],
		select(2)),

	rule('exceptions',
		['exception'],
		tlist(head=0)),
	rule('exceptions',
		['exception', l('or'), 'exceptions'],
		tlist(head=0, rest=2)),
	rule('exception',
		['claims'],
		template(WarrantException, claims=0)),
])


def tokenize(markers, sentence):
	unit = []
	for word in sentence.split(' '):
		if word in markers:
			if len(unit) > 0:
				yield Text(unit)
				unit = []
			yield word
		else:
			unit.append(word)
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

	# parse('Tweety can fly because Tweety is a bird and animals can fly when they have wings unless they are a penguin .')
	parse('The act is unlawful when someone\'s right is violated except when there is a justification .')
	parse('The act is unlawful because someone\'s right was violated except there is a justification .')
	parse('A suspect is innocent unless they are found guilty .')

