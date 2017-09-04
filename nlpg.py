from typing import NamedTuple, List, Set, FrozenSet, Union
from pprint import pprint, pformat
from collections import defaultdict
from itertools import chain
from functools import reduce


DEBUG = False


def debug(*args, **kwargs):
	if DEBUG:
		print("DEBUG:", *args, **kwargs)


class sparselist(list):
	def __setitem__(self, index, value):
		missing = index - len(self) + 1
		if missing > 0:
			self.extend([None] * missing)

		list.__setitem__(self, index, value)
	
	def __getitem__(self, index):
		if isinstance(index, slice):
			return type(self)(list.__getitem__(self, index))
		else:
			try:
				return list.__getitem__(self, index)
			except IndexError:
				return None


class rule(object):
	def __init__(self, name, tokens, template):
		self.name = name
		self.tokens = tokens
		self.template = template


class l(object):
	def __init__(self, word):
		self.word = word

	def __repr__(self):
		return 'l({})'.format(self.word)

	def test(self, word):
		return self.word == word

	def reverse(self, word):
		return self.word


class template(object):
	def __init__(self, pred, **kwargs):
		self.pred = pred
		self.template = kwargs

	def __call__(self, *args):
		try:
			return self.pred(**{
				name: (args[token] if isinstance(token, int) else token)
				for name, token in self.template.items()
			})
		except IndexError:
			raise Exception("Not enough arguments for template {!r}: {}".format(self.template, pformat(args)))

	def reverse(self, structure):
		debug("template.reverse {!r} {!r}".format(self.pred, structure))
		if type(structure) != self.pred:
			return False

		flat = sparselist()
		for name, index in self.template.items():
			if isinstance(index, int):
				flat[index] = getattr(structure, name)
			else:
				if getattr(structure, name) != index:
					return False
		return flat


class select(object):
	def __init__(self, index):
		self.index = index

	def __call__(self, *args):
		return args[self.index]

	def reverse(self, structure):
		flat = sparselist()
		flat[self.index] = structure
		return flat


class tlist(object):
	def __init__(self, head = None, rest = None):
		self.head_index = head
		self.rest_index = rest

	def __call__(self, *args):
		if self.head_index is None:
			return []
		elif self.rest_index is None:
			return [args[self.head_index]]
		else:
			return [args[self.head_index]] + args[self.rest_index]

	def reverse(self, structure):
		if not isinstance(structure, list):
			return False

		flat = sparselist()
		
		if self.head_index is None:
			if len(structure) > 0:
				return False
		else:
			if len(structure) == 0:
				return False
			else:
				flat[self.head_index] = structure[0]

		if self.rest_index is None:
			if len(structure) > 1:
				return False
		else:
			if len(structure) == 1:
				return False
			else:
				flat[self.rest_index] = structure[1:]

		return flat


class empty(object):
	def __call__(self, *args):
		return None

	def reverse(self, structure):
		if structure is None:
			return []
		else:
			return False


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


def is_literal(obj):
	return isinstance(obj, l)


class Parser(object):
	def __init__(self, rules):
		self.rules = rules

	def parse(self, rule_name, words):
		for resolution, remaining_words in self._parse(rule_name, words):
			if len(remaining_words) == 0:
				yield resolution
	
	def _parse(self, rule_name, words):
		for rule in self.rules[rule_name]:
			for acc, remaining_words in self._parse_rule(rule.tokens, words):
				yield rule.template(*acc), remaining_words

	def _parse_rule(self, tokens, words):
		if len(tokens) == 0:
			yield [], words

		elif is_literal(tokens[0]):
			if len(words) == 0 or not tokens[0].test(words[0]):
				return
			else:
				for resolution, remaining_words in self._parse_rule(tokens[1:], words[1:]):
					yield [l(words[0])] + resolution, remaining_words
		else:
			for resolution, remaining_words in self._parse(tokens[0], words):
				for continuation, cont_remaining_words in self._parse_rule(tokens[1:], remaining_words):
					yield [resolution] + continuation, cont_remaining_words

	def reverse(self, rule_name, tree):
		debug("reverse {!r} {!r}".format(rule_name, tree))
		for rule in self.rules[rule_name]:
			flat = rule.template.reverse(tree)
			if flat is not False:
				yield from self._reverse(rule.tokens, flat)

	def _reverse(self, tokens, flat):
		debug("_reverse {!r} {!r}".format(tokens, flat))
		if len(tokens) == 0:
			if len(flat) == 0:
				yield []
			else:
				raise Exception('Well I did not expect this case? Should I yield nothing now?')

		elif is_literal(tokens[0]):
			resolution = tokens[0].reverse(flat[0] if len(flat) > 0 else None)
			if resolution is not False:
				for continuation in self._reverse(tokens[1:], flat[1:]):
					yield [resolution] + continuation
		
		else:
			for resolution in self.reverse(tokens[0], flat[0]):
				for continuation in self._reverse(tokens[1:], flat[1:]):
					yield resolution + continuation


class claim(NamedTuple):
		id: str

class argument(NamedTuple):
	claim: 'claim'
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

	def as_tree(self, root):
		grouped = dict(support=[], attack=[])
		for relation in self.relations:
			if relation.target == root:
				grouped[relation.type].append(list(self.as_tree(claim) for claim in relation.sources))
		return argument(claim=root, supports=grouped['support'], attacks=grouped['attack'])

	@classmethod
	def from_tree(cls, tree: 'argument', diagram:'diagram'=None):
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
			template(argument, claim=0, reasons=2)),
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
			tlist(head=0)),
		rule('reasons',
			['reason', l('and'), 'reasons'],
			tlist(head=0, rest=2))
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
			template(argument, claim=0, support=1)),
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
			select(1))
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
			template(argument, claim=0, support=1)),
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
			select(1))
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
			template(argument, claim=0, support=1, attack=2)),
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
			select(1)),
		rule('attack',
			[],
			empty()),
		rule('attack',
			[l('except'), 'argument'],
			select(1))
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
			['attack_marker', 'extended_claims'],
			select(1)),
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
			template(argument, claim=0, support=1, attack=2)),
		rule('argument_r',
			['claim', 'attack', 'support_r'],
			template(argument, claim=0, support=2, attack=1)),
		rule('argument',
			['claim'],
			template(argument, claim=0, support=None, attack=None)),
		rule('claim', [l('A')], template(claim, id='a')),
		rule('claim', [l('B')], template(claim, id='b')),
		rule('claim', [l('C')], template(claim, id='c')),
		rule('support', [], empty()),
		rule('support', [l('because'), 'argument'], select(1)),
		rule('attack', [], empty()),
		rule('attack', [l('except'), 'argument'], select(1)),
		rule('support_r', [], empty()),
		rule('support_r', [l('because'), 'argument_r'], select(1)),
		rule('attack_r', [], empty()),
		rule('attack_r', [l('except'), 'argument_r'], select(1)),
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
	
	sentence = 'Tweety can fly because Tweety is awesome and because Tweety is a bird and birds can fly but Tweety is a penguin'

	words = sentence.split(' ')

	trees = list(parser.parse('extended_claim', words))

	# pprint(trees[0])

	for n, tree in enumerate(trees):
		print("Tree {}:".format(n + 1))
		diagram = diagram.from_tree(tree)
		for tree_ in diagram.as_trees():
			if tree is not tree_:
				print("oh no they are different?")


if __name__ == '__main__':
	DEBUG=False
	# test_list()
	# test_optional()
	# test_recursion()
	# test_ambiguity()
	test_combined()
	# test_generate()
	# test_boxes_and_arrows()
	# test_sparselist()


# for n, parsed in enumerate(parse(rules['extended_claim'][0], words)):
# 	print("Parse {}:".format(n))
# 	pprint(parsed)
# 	generate(parsed, rules['extended_claim'])
# 	# print("Generated:")
# 	# for p, generated_words in enumerate(generate(parsed)):
# 	#     print("{}: {}".format(p, " ".join(generated_words)))
