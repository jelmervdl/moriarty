from parser import Rule, Literal, RuleRef
from interpretation import Interpretation
from datastructures import OrderedSet


def and_rules(name, singleton, accept_singular=False, first_singleton=None, last_singleton=None):
    """
    Creates a mini-grammar of rules that are needed to parse 'A and B',
    'A, B and C', 'A, B, C and D', etc. where A, B, C and D all are parseable
    using the rule name passed using the singleton argument.
    """
    if last_singleton is None:
        last_singleton = singleton

    if first_singleton is None:
        first_singleton = singleton

    helper = name + "_"
    
    rules = {
        # _ and C
        Rule(name, [RuleRef(helper), Literal('and'), RuleRef(last_singleton)],
            lambda state, data: data[0] + data[2] + Interpretation(local=data[0].local | OrderedSet([data[2].local]))),

        # A, B # (allows for 'A, B and C')
        Rule(helper, [RuleRef(helper), Literal(','), RuleRef(singleton)],
            lambda state, data: data[0] + data[2] + Interpretation(local=data[0].local | OrderedSet([data[2].local]))),

        # A (allows for 'A and B')
        Rule(helper, [RuleRef(first_singleton)],
            lambda state, data: data[0] + Interpretation(local=OrderedSet([data[0].local])))
    }

    if accept_singular:
        rules |= {
            Rule(name, [RuleRef(singleton)],
                lambda state, data: data[0] + Interpretation(local=OrderedSet([data[0].local])))
        }

    return rules