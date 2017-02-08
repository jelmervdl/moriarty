from parser import Rule, Literal, RuleRef
from interpretation import Interpretation


class Sequence(object):
    """Simple sequence utility class, for creating id's"""
    def __init__(self):
        self.value = 0

    def next(self):
        self.value += 1
        return self.value


def macro_and(name, singleton):
    """
    Creates a mini-grammar of rules that are needed to parse 'A and B',
    'A, B and C', 'A, B, C and D', etc. where A, B, C and D all are parseable
    using the rule name passed using the singleton argument.
    """
    helper = name + "_"
    return {
        # _ and C
        Rule(name, [RuleRef(helper), Literal('and'), RuleRef(singleton)],
            lambda state, data: data[0] + data[2] + Interpretation(local=data[0].local | {data[2].local})),

        # A, B # (allows for 'A, B and C')
        Rule(helper, [RuleRef(helper), Literal(','), RuleRef(singleton)],
            lambda state, data: data[0] + data[2] + Interpretation(local=data[0].local | {data[2].local})),

        # A (allows for 'A and B')
        Rule(helper, [RuleRef(singleton)],
            lambda state, data: data[0] + Interpretation(local={data[0].local}))
    }