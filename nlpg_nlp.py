from typing import NamedTuple, List, Set, FrozenSet, Union

from pprint import pprint

import nlpg
from nlpg import Parser, \
	ruleset, rule, terminal, l, \
	empty, tlist, template, select, \
	relation, diagram, \
	NoMatchException

import spacy

# nlpg.DEBUG=True


class sentence(NamedTuple):
	np: List
	vp: List


class prop(NamedTuple):
	subj: List
	verb: str
	obj: List


class tag(terminal):
	def __init__(self, tag):
		self.tag = tag

	def test(self, word):
		return word.tag_ == self.tag

	def consume(self, word):
		return word.text

	def reverse(self, word):
		if word is None:
			raise NoMatchException()
		return word


rules = ruleset([
	rule('sentence',
		['np(s)', 'vp(s)'],
		template(sentence, np=0, vp=1)),
	rule('sentence',
		['np(p)', 'vp(p)'],
		template(sentence, np=0, vp=1)),
	rule('sentence',
		['np(s)', 'vbz', 'np(s)'],
		template(prop, subj=0, verb=1, obj=2)),
	rule('sentence',
		['np(s)', 'vbz', 'jj'],
		template(prop, subj=0, verb=1, obj=2)),
	rule('sentence',
		['det', 'jj', 'n(s)'],
		template(prop, subj=tlist(head=[0,2]), verb='is', obj=1)),
	rule('np(s)',
		['det', 'n(s)'],
		tlist(head=[0, 1])),
	rule('np(p)',
		['n(p)'],
		tlist(head=0)),
	rule('n(s)',
		[tag('NN')],
		select(0)),
	rule('n(p)',
		[tag('NNS')],
		select(0)),
	rule('det',
		[tag('DT')],
		select(0)),
	rule('det',
		[tag('DT')],
		select(0)),
	rule('vp(s)',
		['v(s)'],
		tlist(0)),
	rule('vp(s)',
		['md', 'v(inf)'],
		tlist(head=[0,1])),
	rule('vp(p)',
		['v(p)'],
		tlist(0)),
	rule('v(s)',
		[tag('VBZ')],
		select(0)),
	rule('v(p)',
		[tag('VBP')],
		select(0)),
	rule('md',
		[tag('MD')],
		select(0)),
	rule('v(inf)',
		[tag('VB')],
		select(0)),
	rule('vbz',
		[tag('VBZ')],
		select(0)),
	rule('jj',
		[tag('JJ')],
		select(0)),
])

if __name__ == '__main__':
	nlp = spacy.load('en')
	parser = Parser(rules)
	sentence = nlp('the red bird')

	for word in sentence:
		print("{}: {}".format(word.text, word.tag_))

	trees = set(parser.parse('sentence', sentence))
	for tree in trees:
		pprint(tree)
		for realisation in parser.reverse('sentence', tree):
			pprint(realisation)


