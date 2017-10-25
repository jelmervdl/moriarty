from typing import List, Dict
from enum import Enum
from nlpg_grammar import Text, Claim, Argument, Support, Warrant, WarrantCondition, WarrantException
from itertools import chain


def one(iterable):
	one = next(iterable, None)
	try:
		next(iterable)
		raise Exception('Iterator has multiple values!')
	except StopIteration:
		return one


class Type(Enum):
	SUPPORT = 'support'
	ATTACK = 'attack'


class Diagram(object):
	nodes: Dict[int, dict]
	edges: Dict[int, dict]

	def __init__(self):
		self.sequence = 0
		self.claims = dict()
		self.relations = dict()

	def _next_id(self):
		self.sequence += 1
		return self.sequence

	def _ref(self, node):
		return {
			'isa': node['isa'],
			'id' : node['id']
		}

	def find_roots(self):
		# The root claims have no outgoing relations. I.e. they are never
		# the source of any relation.

		# Find out which claims are referenced
		referenced = frozenset(chain.from_iterable(
			(
				source['id'] for source in relation['sources']
			) for relation in self.relations.values()
		))

		# and then return all claims that are not in that set
		for id, claim in self.claims.items():
			if id not in referenced:
				yield claim

	def find_relations(self, **conditions):
		for relation in self.relations.values():
			if 'type' in conditions:
				if relation['type'] != conditions['type'].value:
					continue

			if 'target' in conditions:
				if self._ref(relation['target']) != self._ref(conditions['target']):
					continue

			if 'sources' in conditions:
				if all(self._ref(source) != self._ref(conditions['sources']) for source in relation['sources']):
					continue

			yield relation

	def add_claim(self, claim):
		claim_id = 'c{}'.format(self._next_id())
		claim = {
			'id': claim_id,
			'isa': 'claim',
			'text': str(claim.text)
		}
		self.claims[claim_id] = claim
		return claim

	def add_relation(self, sources, target, type):
		relation_id = 'r{}'.format(self._next_id())
		relation = {
			'id': relation_id,
			'isa': 'relation',
			'type': type.value,
			'sources': list(self._ref(source) for source in sources),
			'target': self._ref(target)
		}
		self.relations[relation_id] = relation
		return relation

	def add_argument(self, argument):
		node = self.add_claim(argument.claim)
		
		for support in argument.supports:
			self.add_support(node, support)

		return node

	def add_support(self, node, support):
		datum_nodes = list(self.add_argument(datum) for datum in support.datums)
		edge = self.add_relation(
			sources=datum_nodes,
			target=node,
			type=Type.SUPPORT)

		if support.warrant:
			warrant_node = self.add_warrant(support.warrant)
			self.add_relation(sources=[warrant_node], target=edge, type=Type.SUPPORT)

		if support.undercutter:
			undercutter_node = self.add_argument(support.undercutter)
			self.add_relation(sources=[undercutter_node], target=edge, type=Type.ATTACK)

	def add_warrant(self, warrant):
		node = self.add_claim(warrant.claim)

		for condition in warrant.conditions:
			claim_nodes = list(self.add_claim(claim) for claim in condition.claims)
			edge = self.add_relation(
				sources=claim_nodes,
				target=node,
				type=Type.SUPPORT)

			for exception in condition.exceptions:
				exception_nodes = list(self.add_claim(claim) for claim in exception.claims)
				exception_edge = self.add_relation(
					sources=exception_nodes,
					target=edge,
					type=Type.ATTACK)

		return node

	@classmethod
	def from_arguments(cls, arguments: List[Argument]) -> 'Diagram':
		diagram = cls()
		for argument in arguments:
			diagram.add_argument(argument)
		return diagram

	def to_arguments(self) -> List[Argument]:
		#todo: split up the argument into multiple arguments
		yield tuple(self.to_argument(claim) for claim in self.find_roots())
	
	def to_argument(self, claim):
		return Argument(
			claim=self.to_claim(claim),
			supports=tuple(self.to_support(support) for support in self.find_relations(target=claim, type=Type.SUPPORT)))

	def to_support(self, support):
		return Support(
			datums=tuple(self.to_argument(datum) for datum in support['sources']),
			warrant=one(self.to_warrant(warrant) for warrant in self.find_relations(target=support, type=Type.SUPPORT)),
			undercutter=one(self.to_argument(undercutter['sources'][0]) for undercutter in self.find_relations(target=support, type=Type.ATTACK)))

	def to_warrant(self, warrant):
		return Warrant(
			claim=one(self.to_claim(claim) for claim in warrant['sources']),
			conditions=tuple(self.to_condition(condition) for condition in self.find_relations(target=warrant['sources'][0], type=Type.SUPPORT)))
	
	def to_condition(self, condition):
		return WarrantCondition(
			claims=tuple(self.to_claim(claim) for claim in condition['sources']),
			exceptions=tuple(self.to_exception(exception) for exception in self.find_relations(target=condition, type=Type.ATTACK)))

	def to_exception(self, exception):
		return WarrantException(claims=tuple(self.to_claim(claim) for claim in exception['sources']))

	def to_claim(self, claim):
		assert claim['isa'] == 'claim'
		if 'text' not in claim:
			claim = self.claims[claim['id']]
		return Claim(text=Text([claim['text']]))

	@classmethod
	def from_object(cls, obj: dict) -> 'Diagram':
		"""
		Convert a JSON object back to a diagram. This assumes
		that the edges that use previous nodes and edges come
		after those previous nodes and edges. No circular stuff!
		"""
		
		# lists, but by id
		diagram = cls()

		assert obj['isa'] == 'diagram'

		for claim in obj['claims']:
			assert claim['isa'] == 'claim'
			diagram.claims[claim['id']] = claim

		for relation in obj['relations']:
			assert relation['isa'] == 'relation'
			diagram.relations[relation['id']] = relation

		return diagram

	def to_object(self) -> dict:
		return {
			'isa': 'diagram',
			'claims': list(self.claims.values()),
			'relations': list(self.relations.values()),
		}


if __name__ == '__main__':
	from nlpg_grammar import parse, reverse
	from deepdiff import DeepDiff
	from pprint import pprint
	import json

	sentence = 'This ball is red because it looks red and balls are red when they look red except the light is red.'

	for arguments in list(parse(sentence)):
		# Convert the argument structure to a diagram
		diagram = Diagram.from_arguments(arguments)

		# Convert the diagram to an object
		obj = diagram.to_object()

		# Convert the object to a json string
		obj_json = json.dumps(obj)

		# Recover the object from the json string
		recovered_obj = json.loads(obj_json)

		# Recover the diagram from the object
		recovered_diagram = Diagram.from_object(recovered_obj)
		
		# Convert that diagram back to an argument structure
		for recovered in recovered_diagram.to_arguments():
			# Print realisations (which should among them contain the sentence)
			for realisation in reverse(recovered):
				print(realisation)

		