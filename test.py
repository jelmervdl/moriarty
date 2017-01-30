from parser import Parser, Rule, RuleRef, passthru
from grammar import claim, general, specific
import traceback
import sys

grammar = claim.grammar | general.grammar | specific.grammar | {
    Rule('CLAIM', [RuleRef('GENERAL_CLAIM')], passthru),
    Rule('CLAIM', [RuleRef('SPECIFIC_CLAIM')], passthru),
}

sentences = [
    ['Tweety', 'is', 'a', 'bird'],
    ['birds', 'can', 'fly'],
    ['Tweety', 'can', 'fly'],
    ['Tweety', 'can', 'not', 'fly']
]

parser = Parser(grammar, 'CLAIM')

for sentence in sentences:
    try:
        print("> Input: {}".format(" ".join(sentence)))
        parses = parser.parse(sentence)
        for n, parse in enumerate(parses):
            print("{0: 2d}: {1!s}\n    {1!r}".format(n, parse))
    except Exception:
        traceback.print_exc(file=sys.stderr)