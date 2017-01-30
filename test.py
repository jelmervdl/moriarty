from parser import Parser, Rule, RuleRef, passthru
from grammar.shared import negation, claim, general, specific
import traceback
import sys

grammar = claim.grammar | general.grammar | specific.grammar | negation.grammar | {
    Rule('CLAIM', [RuleRef('GENERAL_CLAIM')], passthru),
    Rule('CLAIM', [RuleRef('SPECIFIC_CLAIM')], passthru),
}

sentences = [
    ['Tweety', 'is', 'a', 'bird'],
    ['birds', 'can', 'fly'],
    ['the', 'birds', 'can', 'fly'],
    ['Tweety', 'can', 'fly'],
    ['Tweety', 'can', 'not', 'fly'],
    ['Tweety', 'and', 'Birdy', 'are', 'pretty']
]

parser = Parser(grammar, 'CLAIM')

print("Grammar:")
for rule in sorted(grammar, key=lambda rule: rule.name):
    print("  " + str(rule))
print()

print("Tests:")
for sentence in sentences:
    try:
        print("  > Input: {}".format(" ".join(sentence)))
        parses = parser.parse(sentence)
        for n, parse in enumerate(parses):
            print("   {0: 2d}: {1!s}\n       {1!r}".format(n, parse))
    except Exception:
        traceback.print_exc(file=sys.stderr)