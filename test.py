from parser import Parser, Rule, RuleInstance, RuleRef, passthru
from grammar.shared import negation, claim, general, specific
import traceback
import sys


def override_callbacks(rules, callback = None):
    """
    Override the callback in all rules in a grammar.
    
    If no callback argument is provided, each rule will yield a RuleInstance
    which can be used to see how a rule was parsed.
    """
    if callback is None:
        def callback(rule):
            return lambda state, data: RuleInstance(rule, data)

    for rule in rules:
        rule.callback = callback(rule)


grammar = general.grammar | specific.grammar | negation.grammar | {
    Rule('ARGUMENT', [RuleRef('GENERAL_CLAIM')], passthru),
    Rule('ARGUMENT', [RuleRef('SPECIFIC_CLAIM')], passthru),
}

sentences = [
    ['Tweety', 'is', 'a', 'bird'],
    ['birds', 'can', 'fly'],
    ['the', 'birds', 'can', 'fly'],
    ['Tweety', 'can', 'fly'],
    ['Tweety', 'can', 'not', 'fly'],
    ['Tweety', 'and', 'Birdy', 'are', 'pretty']
]

# Uncomment this call to see the parse trees.
# override_callbacks(grammar)

parser = Parser(grammar, 'ARGUMENT')

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