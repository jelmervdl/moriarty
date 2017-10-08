from typing import NamedTuple, List, Set, FrozenSet, Union, Optional
from collections.abc import Sequence
from pprint import pprint, pformat
from collections import defaultdict
from itertools import chain
from functools import reduce


DEBUG = False


def debug(*args, **kwargs):
	if DEBUG:
		print("DEBUG:", *args, **kwargs)


class sparselist(list):
	"""
	Like a normal list, except it extends automatically if you try to set an
	index that does not exist yet. Unset indexes are None. It throws an
	exception if you try to set an already set index with another value. (In 
	that sense it is pretty read-only.)
	You can combine multiple sparselists using the union (or) operator. Note
	that the index-can-only-be-set-once rule still applies, so this operation
	only succeeds if there are no overlapping indexes between the two lists.
	"""

	def __setitem__(self, index, value):
		assert isinstance(index, int)
		missing = index - len(self) + 1
		if missing > 0:
			self.extend([None] * missing)
		if self[index] is not None:
			raise Exception('Trying to overwrite already set value in sparselist')
		list.__setitem__(self, index, value)
	
	def __getitem__(self, index):
		if isinstance(index, slice):
			return type(self)(list.__getitem__(self, index))
		else:
			try:
				return list.__getitem__(self, index)
			except IndexError:
				return None

	def __or__(self, other):
		assert isinstance(other, type(self))
		merged = type(self)(self)
		if len(merged) < len(other):
			merged.extend([None] * (len(other) - len(merged)))
		for n in range(len(other)):
			if other[n] is not None:
				merged[n] = other[n]
		return merged


class rule(object):
	def __init__(self, name, tokens, template):
		self.name = name
		self.tokens = tokens
		self.template = template

	def __repr__(self):
		return "Rule<{}>{!r}".format(self.name, self.tokens)


class terminal(object):
	def test(self, word):
		return False

	def reverse(self, word):
		return word

	def consume(self, word):
		return word


class l(terminal):
	def __init__(self, word):
		self.word = word

	def __repr__(self):
		return 'l({})'.format(self.word)

	def test(self, word):
		return self.word == word

	def consume(self, word):
		return self.__class__(word)

	def reverse(self, word):
		if isinstance(word, self.__class__):
			if word.word != self.word:
				raise NoMatchException('Different literal')
		elif isinstance(word, str):
			if word != self.word:
				raise NoMatchException('Different word')
		return self.word


class NoMatchException(Exception):
	pass


class template(object):
	def __init__(self, pred, **kwargs):
		self.pred = pred
		self.template = kwargs

	def consume(self, args):
		try:
			kwargs = dict()
			for name, token in self.template.items():
				if is_consumer(token):
					kwargs[name] = token.consume(args)
				else:
					kwargs[name] = token
			return self.pred(**kwargs)
		except IndexError:
			raise Exception("Not enough arguments for template {!r}: {}".format(self.template, pformat(args)))

	def reverse(self, structure):
		debug("template.reverse {!r} {!r}".format(self.pred, structure))
		if type(structure) != self.pred:
			raise NoMatchException()

		flat = sparselist()
		for name, index in self.template.items():
			if is_reversable(index):
				flat = flat | index.reverse(getattr(structure, name))
			else:
				if getattr(structure, name) != index:
					raise NoMatchException("Property {} does not match ({!r} in structure vs {!r} in template)".format(name, getattr(structure, name), index))
		return flat


class slot(object):
	def __init__(self, index):
		self.index = index

	def consume(self, args):
		return args[self.index]

	def reverse(self, structure):
		flat = sparselist()
		flat[self.index] = structure
		return flat


class tlist(object):
	def __init__(self, head = None, rest = None):
		if head is None:
			self.head_index = []
		elif isinstance(head, list):
			self.head_index = head
		else:
			self.head_index = [head]
		self.rest_index = rest

	def consume(self, args):
		if self.rest_index is None:
			return tuple(index.consume(args) for index in self.head_index)
		else:
			return tuple(index.consume(args) for index in self.head_index) + self.rest_index.consume(args)
	def reverse(self, structure):
		if not isinstance(structure, Sequence):
			raise NoMatchException('structure is not a sequence')

		flat = sparselist()

		if len(structure) < len(self.head_index):
			raise NoMatchException('head_index is longer than structure')
		else:
			for n, index in enumerate(self.head_index):
				flat |= index.reverse(structure[n])

		if self.rest_index is None:
			if len(structure) > len(self.head_index):
				raise NoMatchException('structure is longer while expected end of list')
		else:
			if len(structure) <= len(self.head_index):
				raise NoMatchException('structure is about the length of the head_index while expecting also a tail')
			else:
				flat |= self.rest_index.reverse(structure[len(self.head_index):])

		return flat


class empty(object):
	def consume(self, args):
		return None

	def reverse(self, structure):
		if structure is None:
			return []
		else:
			raise NoMatchException()


class ruleset(object):
	def __init__(self, rules):
		self.rules = defaultdict(lambda: [])
		for rule in rules:
			self.rules[rule.name].append(rule)

	def __getitem__(self, name):
		if name in self.rules:
			return self.rules[name]
		else:
			raise Exception('No rules for <{}>' .format(name))

	def __iter__(self):
		return chain.from_iterable(self.rules.values())

	def lhs(self):
		return self.rules.keys()

	def rhs(self):
		def find_references(rules):
			for rule in rules:
				for token in rule.tokens:
					if isinstance(token, str):
						yield token
		return frozenset(find_references(self))

	def missing(self):
		return self.rhs() - self.lhs()

	def unreachable(self):
		return self.lhs() - self.rhs()

	def markers(self):
		def find_markers(rules):
			for rule in rules:
				for token in rule.tokens:
					if isinstance(token, l):
						yield token.word
		return frozenset(find_markers(self))


def is_literal(obj):
	return isinstance(obj, terminal)


def is_consumer(obj):
	return hasattr(obj, 'consume')


def is_reversable(obj):
	return hasattr(obj, 'reverse')


class ParseException(Exception):
	pass


class Parser(object):
	def __init__(self, rules):
		self.rules = rules

	def parse(self, rule_name, words):
		for resolution, remaining_words in self._parse(rule_name, words):
			if len(remaining_words) == 0:
				yield resolution
	
	def _parse(self, rule_name, words):
		for rule in self.rules[rule_name]:
			try:
				for acc, remaining_words in self._parse_rule(rule.tokens, words):
					yield rule.template.consume(acc), remaining_words
			except:
				raise ParseException("Error while parsing {}<{!r}>".format(rule_name, rule))

	def _parse_rule(self, tokens, words):
		if len(tokens) == 0:
			yield [], words

		elif is_literal(tokens[0]):
			if len(words) == 0 or not tokens[0].test(words[0]):
				return
			else:
				for resolution, remaining_words in self._parse_rule(tokens[1:], words[1:]):
					yield [tokens[0].consume(words[0])] + resolution, remaining_words
		else:
			for resolution, remaining_words in self._parse(tokens[0], words):
				for continuation, cont_remaining_words in self._parse_rule(tokens[1:], remaining_words):
					yield [resolution] + continuation, cont_remaining_words

	def reverse(self, rule_name, tree):
		debug("reverse {!r} {!r}".format(rule_name, tree))
		for rule in self.rules[rule_name]:
			try:
				flat = rule.template.reverse(tree)
				debug('<{}>.reverse({!r}) returned true, continuing with {!r}'.format(rule_name, rule, flat))
				yield from self._reverse(rule.tokens, flat)
			except NoMatchException as e:
				debug('<{}>.reverse({!r}) failed because {}'.format(rule_name, rule, e))

	def _reverse(self, tokens, flat):
		assert isinstance(flat, list)
		debug("_reverse {!r} {!r}".format(tokens, flat))
		if len(tokens) == 0:
			if len(flat) == 0:
				yield []
			else:
				raise Exception('Well I did not expect this case? Should I yield nothing now?')

		elif is_literal(tokens[0]):
			try:
				resolution = tokens[0].reverse(flat[0] if len(flat) > 0 else None)
				for continuation in self._reverse(tokens[1:], flat[1:]):
					yield [resolution] + continuation
			except NoMatchException:
				pass
		
		else:
			for resolution in self.reverse(tokens[0], flat[0]):
				for continuation in self._reverse(tokens[1:], flat[1:]):
					yield resolution + continuation


class claim(NamedTuple):
		id: str

class argument(NamedTuple):
	claim: claim
	attacks: List[List['argument']]
	supports: List[List['argument']]


class relation(NamedTuple):
	sources: FrozenSet['claim']
	target: Union['claim', 'relation']
	type: str


class diagram(NamedTuple):
	claims: Set['claim']
	relations: Set['relation']

	def as_trees(self):
		# First, find the topmost claim (the claim that is the target, but never the source)
		roots = self.claims - frozenset(chain.from_iterable(relation.sources for relation in self.relations))
		for root in roots:
			yield self.as_tree(root)

	def as_tree(self, root, visited = frozenset()):
		grouped = dict(support=[], attack=[])
		for relation in self.relations:
			if relation.target == root:
				grouped[relation.type].append(list(
					self.as_tree(claim, visited | frozenset([claim])) if claim not in visited else argument(claim=claim, supports=[], attacks=[])
					for claim in relation.sources))
		return argument(claim=root, supports=grouped['support'], attacks=grouped['attack'])

	@classmethod
	def from_tree(cls, tree: 'argument', diagram: Optional['diagram'] = None):
		if diagram is None:
			diagram = cls(set(), set())

		assert isinstance(tree.claim, claim)
		diagram.claims.add(tree.claim)

		for attack in tree.attacks:
			diagram.claims.update(arg.claim for arg in attack)
			diagram.relations.add(relation(sources=frozenset(arg.claim for arg in attack), target=tree.claim, type='attack'))
			for arg in attack:
				cls.from_tree(arg, diagram)

		for support in tree.supports:
			diagram.claims.update(arg.claim for arg in support)
			diagram.relations.add(relation(sources=frozenset(arg.claim for arg in support), target=tree.claim, type='support'))
			for arg in support:
				cls.from_tree(arg, diagram)

		return diagram


def test_list():
	class claim(NamedTuple):
		id: str

	class argument(NamedTuple):
		claim: 'claim'
		reasons: List['claim']

	rules = ruleset([
		rule('argument',
			['claim', l('because'), 'reasons'],
			template(argument, claim=slot(0), reasons=slot(2))),
		rule('claim',
			[l('A')],
			template(claim, id='a')),
		rule('reason',
			[l('B')],
			template(claim, id='b')),
		rule('reason',
			[l('C')],
			template(claim, id='c')),
		rule('reasons',
			['reason'],
			tlist(head=slot(0))),
		rule('reasons',
			['reason', l('and'), 'reasons'],
			tlist(head=slot(0), rest=slot(2)))
	])
	
	parser = Parser(rules)
	
	words = "A because B and C".split(' ')
	
	trees = list(parser.parse('argument', words))

	print(repr(trees))

	for tree in trees:
		for realisation in parser.reverse('argument', tree):
			print(realisation)


def test_optional():
	class claim(NamedTuple):
		id: str

	class argument(NamedTuple):
		claim: 'claim'
		support: 'claim'

	rules = ruleset([
		rule('argument',
			['claim', 'support'],
			template(argument, claim=slot(0), support=slot(1))),
		rule('claim',
			[l('A')],
			template(claim, id='a')),
		rule('claim',
			[l('B')],
			template(claim, id='b')),
		rule('support',
			[],
			empty()),
		rule('support',
			[l('because'), 'claim'],
			slot(1))
	])
	
	parser = Parser(rules)
	
	words = "A because B".split(' ')
	
	trees = list(parser.parse('argument', words))

	print(repr(trees))

	for tree in trees:
		for realisation in parser.reverse('argument', tree):
			print(realisation)


def test_recursion():
	class claim(NamedTuple):
		id: str

	class argument(NamedTuple):
		claim: 'claim'
		support: 'claim'

	rules = ruleset([
		rule('argument',
			['claim', 'support'],
			template(argument, claim=slot(0), support=slot(1))),
		rule('claim',
			[l('A')],
			template(claim, id='a')),
		rule('claim',
			[l('B')],
			template(claim, id='b')),
		rule('claim',
			[l('C')],
			template(claim, id='c')),
		rule('support',
			[],
			empty()),
		rule('support',
			[l('because'), 'argument'],
			slot(1))
	])
	
	parser = Parser(rules)
	
	words = "A because B because C because A".split(' ')
	
	trees = list(parser.parse('argument', words))

	print(repr(trees))

	for tree in trees:
		for realisation in parser.reverse('argument', tree):
			print(realisation)


def test_ambiguity():
	class claim(NamedTuple):
		id: str

	class argument(NamedTuple):
		claim: 'claim'
		support: 'claim'
		attack: 'claim'

	rules = ruleset([
		rule('argument',
			['claim', 'support', 'attack'],
			template(argument, claim=slot(0), support=slot(1), attack=slot(2))),
		rule('claim',
			[l('A')],
			template(claim, id='a')),
		rule('claim',
			[l('B')],
			template(claim, id='b')),
		rule('claim',
			[l('C')],
			template(claim, id='c')),
		rule('support',
			[],
			empty()),
		rule('support',
			[l('because'), 'argument'],
			slot(1)),
		rule('attack',
			[],
			empty()),
		rule('attack',
			[l('except'), 'argument'],
			slot(1))
	])
	
	parser = Parser(rules)
	
	words = "A because B except C".split(' ')
	
	trees = list(parser.parse('argument', words))

	pprint(trees)

	for tree in trees:
		for realisation in parser.reverse('argument', tree):
			print(realisation)


def test_combined():
	class claim(NamedTuple):
		id: str

	class argument(NamedTuple):
		claim: 'claim'
		attacks: List['claim']
		supports: List['claim']

	rules = ruleset([
		rule('extended_claims',
			['extended_claim'],
			tlist(slot(0))),
		rule('extended_claims',
			['extended_claim', l('and'), 'extended_claims'],
			tlist(slot(0), slot(2))),
		rule('extended_claim',
			['claim', 'supports', 'attacks'],
			template(argument, claim=slot(0), supports=slot(1), attacks=slot(2))),
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
			tlist(slot(0))),
		rule('supports',
			['support', l('and'), 'supports'],
			tlist(slot(0), slot(2))),
		rule('support',
			[l('because'), 'extended_claims'],
			slot(1)),
		rule('attacks',
			[],
			tlist()),
		rule('attacks',
			['attack'],
			tlist(slot(0))),
		rule('attacks',
			['attack', l('and'), 'attacks'],
			tlist(slot(0), slot(2))),
		rule('attack',
			['attack_marker', 'extended_claims'],
			slot(1)),
		rule('attack_marker', [l('but')], empty()),
		rule('attack_marker', [l('except'), l('that')], empty())
	])

	parser = Parser(rules)
	
	sentence = 'Tweety can fly because Tweety is awesome and because Tweety is a bird and birds can fly but Tweety is a penguin'

	words = sentence.split(' ')

	trees = list(parser.parse('extended_claim', words))

	pprint(trees)

	for tree in trees:
		for realisation in parser.reverse('extended_claim', tree):
			print(' '.join(realisation))


def test_generate():
	class claim(NamedTuple):
		id: str

	class argument(NamedTuple):
		claim: 'claim'
		support: 'claim'
		attack: 'claim'

	rules = ruleset([
		rule('argument_r',
			['claim', 'support', 'attack_r'],
			template(argument, claim=slot(0), support=slot(1), attack=slot(2))),
		rule('argument_r',
			['claim', 'attack', 'support_r'],
			template(argument, claim=slot(0), support=slot(2), attack=1)),
		rule('argument',
			['claim'],
			template(argument, claim=slot(0), support=None, attack=None)),
		rule('claim', [l('A')], template(claim, id='a')),
		rule('claim', [l('B')], template(claim, id='b')),
		rule('claim', [l('C')], template(claim, id='c')),
		rule('support', [], empty()),
		rule('support', [l('because'), 'argument'], slot(1)),
		rule('attack', [], empty()),
		rule('attack', [l('except'), 'argument'], slot(1)),
		rule('support_r', [], empty()),
		rule('support_r', [l('because'), 'argument_r'], slot(1)),
		rule('attack_r', [], empty()),
		rule('attack_r', [l('except'), 'argument_r'], slot(1)),
	])
	
	parser = Parser(rules)

	tree = argument(
		claim=claim(id='a'),
		support=argument(
			claim=claim(id='b'),
			support=None,
			attack=argument(
				claim=claim(id='c'),
				support=None,
				attack=None)),
		attack=None)

	tree = argument(
		claim=claim(id='a'),
		support=argument(
			claim=claim(id='b'),
			support=argument(
				claim=claim(id='b'),
				support=None,
				attack=None),
			attack=None),
		attack=argument(
			claim=claim(id='c'),
			support=None,
			attack=None))

	# tree = argument(claim=claim(id='a'), support=None, attack=None)
	
	for realisation in parser.reverse('argument_r', tree):
		print(realisation)


def test_sparselist():
	x = sparselist()
	x[3] = 5
	print("{}({!r})".format(type(x), x))
	print("{}({!r})".format(type(x[1:]), x[1:]))


def test_boxes_and_arrows():
	rules = ruleset([
		rule('extended_claims',
			['extended_claim'],
			tlist(slot(0))),
		rule('extended_claims',
			['extended_claim', l('and'), 'extended_claims'],
			tlist(slot(0), slot(2))),
		rule('extended_claim',
			['claim', 'supports', 'attacks'],
			template(argument, claim=slot(0), supports=slot(1), attacks=slot(2))),
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
			tlist(slot(0))),
		rule('supports',
			['support', l('and'), 'supports'],
			tlist(slot(0), slot(2))),
		rule('support',
			[l('because'), 'extended_claims'],
			slot(1)),
		rule('attacks',
			[],
			tlist()),
		rule('attacks',
			['attack'],
			tlist(slot(0))),
		rule('attacks',
			['attack', l('and'), 'attacks'],
			tlist(slot(0), slot(2))),
		rule('attack',
			[l('but'), 'extended_claims'],
			slot(1))
	])

	parser = Parser(rules)
	
	sentence = 'Tweety can fly because Tweety is awesome and because Tweety is a bird and birds can fly but Tweety is a penguin'

	words = sentence.split(' ')

	trees = list(parser.parse('extended_claim', words))

	# pprint(trees[0])

	for n, tree in enumerate(trees):
		print("Tree {}:".format(n + 1))
		diag = diagram.from_tree(tree)
		for tree_ in diag.as_trees():
			if tree is not tree_:
				print("oh no they are different?")


if __name__ == '__main__':
	DEBUG=False
	test_list()
	test_optional()
	test_recursion()
	test_ambiguity()
	test_combined()
	test_generate()
	test_boxes_and_arrows()
	test_sparselist()


# for n, parsed in enumerate(parse(rules['extended_claim'][0], words)):
# 	print("Parse {}:".format(n))
# 	pprint(parsed)
# 	generate(parsed, rules['extended_claim'])
# 	# print("Generated:")
# 	# for p, generated_words in enumerate(generate(parsed)):
# 	#     print("{}: {}".format(p, " ".join(generated_words)))

