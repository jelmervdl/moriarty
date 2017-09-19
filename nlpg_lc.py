from typing import List, Any, Iterator, NamedTuple
from nlpg import Parser, rule, terminal, select
from pprint import pprint

# https://github.com/ssarkar2/LeftCornerParser/blob/master/LCParser.py

def remove_embedded_tokens(rules: List[rule]) -> List[rule]:
	out = []

	for old_rule in rules:
		# If the rule is a terminal rule, just forward it
		if len(old_rule.tokens) == 1 and isinstance(old_rule.tokens[0], terminal):
			out.append(old_rule)

		# If the rule has no terminals, also just forward it
		elif not any(isinstance(token, terminal) for token in old_rule.tokens):
			out.append(old_rule)
		
		# The rule has one or more terminals
		else:
			new_rule_tokens = []

			for token in old_rule.tokens:
				if isinstance(token, terminal):
					# Make up a name for the terminal rule
					terminal_name = 't_{}'.format(hash(token))
					# Create a new rule for the terminal
					out.append(rule(terminal_name, [token], select(0)))
					# 'Update' the rule that contained to terminal to refer to 
					# the new terminal rule
					new_rule_tokens.append(terminal_name)

			# Instead of the original rule add a copy that refers to the terminals
			# using the terminal rules.
			out.append(rule(old_rule.name, new_rule_tokens, old_rule.template))

	return out


class Frame(NamedTuple):
	rule: rule
	index: int
	match: Any

	@property
	def complete(self):
		return len(self.rule.tokens) == self.index

	def __repr__(self):
		return "Frame<{}>({})=({!r})".format(self.rule.name,
			" ".join(map(str, self.rule.tokens[0:self.index] + ['*'] + self.rule.tokens[self.index:])),
			self.match)


class Config(NamedTuple):
	stack: List[Frame]
	index: int


class Parse(object):
	def __init__(self, rules: List[rule], words: List[Any], goal: str):
		self.chart = None
		self.rules = remove_embedded_tokens(rules)
		self.words = list(words)
		self.goal = goal

	def __iter__(self):
		assert self.chart is None, "Parse object does not support concurrent iteration"

		self.chart = [Config([], -1)]
		
		while len(self.chart) > 0:
			if self._has_found(self.goal):
				yield self.chart[-1].stack[0].match
			
			self.step()

		self.chart = None

	def _has_found(self, rule_name: str) -> bool:
		return any(len(config.stack) > 0
			  and config.stack[0].rule.name == rule_name
			  and config.stack[0].complete
			for config in self.chart)

	def step(self):
		config = self.chart.pop()
		self.chart.extend(self._scan(config))
		self.chart.extend(self._predict(config))
		self.chart.extend(self._complete(config))

	def _scan(self, config: Config) -> Iterator[Config]:
		if config.index < len(self.words) - 1:
			word = self.words[config.index + 1]
			for rule, match in self._find_rules(word):
				yield Config(config.stack + [Frame(rule, 1, match)], config.index + 1)

	def _predict(self, config: Config) -> Iterator[Config]:
		"""
		Based on the last rule on the stack, predict which higher rule could be
		positioned above the last rule.
		"""
		if len(config.stack) > 0:
			if config.stack[-1].complete:
				for rule in self._find_left_corner(config.stack[-1].rule):
					yield Config(config.stack[0:-1] + [Frame(rule, 1, [config.stack[-1].match])], config.index)

	def _complete(self, config: Config) -> Iterator[Config]:
		"""
		If the last rule on the stack is complete, and the second one isn't yet
		then check whether the second one can be progressed with the completed
		rule, and if this is the case, do so.
		"""
		if len(config.stack) > 1:
			if config.stack[-1].complete:
				first, second = config.stack[:-3:-1] # last and second-last two elements
				if not second.complete and first.rule.name == second.rule.tokens[second.index]:
					# Append the results of the child token to the progress so far
					match = second.match + [first.match]

					# If this step will complete this rule, consume the result
					if second.index + 1 == len(second.rule.tokens):
						match = second.rule.template.consume(match)
					
					# Yield a new config where the last two frames, the one with the parent and the child,
					# are replaced with one where the parent has progressed one step. 
					yield Config(config.stack[0:-2] + [Frame(second.rule, second.index + 1, match)], config.index)

	def _find_left_corner(self, corner: rule) -> Iterator[rule]:
		print("Predicting for {}".format(corner))
		for rule in self.rules:
			if len(rule.tokens) > 0 and rule.tokens[0] == corner.name:
				yield rule

	def _find_rules(self, word: Any) -> Iterator[rule]:
		print("Detecting {!r}".format(word))
		for rule in self.rules:
			if len(rule.tokens) == 1 \
				and isinstance(rule.tokens[0], terminal) \
				and rule.tokens[0].test(word):
				yield rule, rule.tokens[0].consume(word)


class LCParser(Parser):
	def parse(self, rule_name, words):
		return Parse(self.rules, words, rule_name)

if __name__ == '__main__':
	from nlpg import ruleset, rule, tlist, template, l, select, empty
	from pprint import pprint

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

	parser = LCParser(rules)
	
	sentence = 'Tweety can fly because Tweety is awesome and because Tweety is a bird and birds can fly but Tweety is a penguin'

	words = sentence.split(' ')

	trees = list(parser.parse('extended_claim', words))

	pprint(trees)

	for tree in trees:
		for realisation in parser.reverse('extended_claim', tree):
			print(' '.join(realisation))
