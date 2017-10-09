from nlpg import Parser
from nlpg_grammar import rules, tokenize
from pprint import pprint

sentences = ' '.join([
	'A person must repair the damage \
		when they committed a tortious act,\
		against another person, \
		that can be attributed to him, \
		and that this other person has suffered as a result thereof.',
	'They committed a tortious act \
		if there was a violation of someone else\'s right \
		and an act/omission in violation of a duty imposed by law \
		or of what according to unwritten law has to be regarded as proper social conduct\
		unless there was a justification for this behaviour.',
	'A tortious act can be attributed to the tortfeasor \
		if it results from his fault\
		or from a cause for which he is accountable by virtue of law/generally accepted principles.',
])

assert rules.unreachable() == set()

parser = Parser(rules)

tokens = list(tokenize(rules.markers(), sentences))

parses = list(parser.parse('sentences', tokens))

pprint(parses)

# for parse in parses:
# 	for n, realisation in enumerate(parser.reverse('sentences', parse)):
# 		print("{}: {}".format(n, ' '.join(map(str, realisation))))


