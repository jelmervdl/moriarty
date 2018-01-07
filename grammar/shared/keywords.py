import interpretation

keywords = frozenset([
	'when',
	'if',
	'a',
	'the',
	'and',
	'or',
	'because',
	'unless',
	'except',
	'.',
	'is',
	'can'
])

class Expression(interpretation.Expression):
    def test(self, literal: str, position: int, state: 'State') -> bool:
    	return literal not in keywords and super().test(literal, position, state)
