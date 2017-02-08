from parser import Rule, Literal, RuleRef
from interpretation import Interpretation
from datastructures import OrderedSet


def and_rules(name, singleton):
    """
    Creates a mini-grammar of rules that are needed to parse 'A and B',
    'A, B and C', 'A, B, C and D', etc. where A, B, C and D all are parseable
    using the rule name passed using the singleton argument.
    """
    helper = name + "_"
    return {
        # _ and C
        Rule(name, [RuleRef(helper), Literal('and'), RuleRef(singleton)],
            lambda state, data: data[0] + data[2] + Interpretation(local=data[0].local | OrderedSet([data[2].local]))),

        # A, B # (allows for 'A, B and C')
        Rule(helper, [RuleRef(helper), Literal(','), RuleRef(singleton)],
            lambda state, data: data[0] + data[2] + Interpretation(local=data[0].local | OrderedSet([data[2].local]))),

        # A (allows for 'A and B')
        Rule(helper, [RuleRef(singleton)],
            lambda state, data: data[0] + Interpretation(local=OrderedSet([data[0].local])))
    }