from grammar.shared import category, prototype, verb
from parser import Rule, RuleRef, Literal
from interpretation import Interpretation


class Negation(object):
    def __init__(self, object):
        self.object = object

    def __repr__(self):
        return "Negation({!r})".format(self.object)

    def __str__(self):
        return "not {!s}".format(self.object)

    @classmethod
    def from_rule(cls, state, data):
        return data[1] + Interpretation(local=cls(data[1].local))


grammar = category.grammar | prototype.grammar | verb.grammar | {
    Rule('CATEGORY', [Literal('not'), RuleRef('CATEGORY')],
        Negation.from_rule),

    Rule('PROTOTYPE', [Literal('not'), RuleRef('PROTOTYPE')],
        Negation.from_rule),

    Rule('PROTOTYPES', [Literal('not'), RuleRef('PROTOTYPES')],
        Negation.from_rule),

    Rule('VERB_INF', [Literal('not'), RuleRef('VERB_INF')],
        Negation.from_rule)
}