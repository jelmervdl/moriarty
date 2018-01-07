from grammar.shared import category, prototype, verb
from parser import Rule, RuleRef
from interpretation import Interpretation, Expression
from decorators import memoize


class Negation(object):
    def __init__(self, object):
        self.object = object

    def __repr__(self):
        return "Negation({!r})".format(self.object)

    def __str__(self):
        return "{} {!s}".format('no' if isinstance(self.object, category.Category) else 'not',  self.object)

    @property
    def singular(self):
        return Negation(self.object.singular)

    @property
    def plural(self):
        return Negation(self.object.plural)

    @classmethod
    def from_rule(cls, state, data):
        if isinstance(data[1].local, cls):
            neg = data[1].local.object  # Unwrap double negations
        else:
            neg = cls(data[1].local)
        return data[1] + Interpretation(local=neg)


@memoize
def grammar(**kwargs):
    return category.grammar(**kwargs) | prototype.grammar(**kwargs) | verb.grammar(**kwargs) | {
        Rule('CATEGORY', [Expression('not?'), RuleRef('CATEGORY')],
            Negation.from_rule),

        Rule('PROTOTYPE', [Expression('not'), RuleRef('PROTOTYPE')],
            Negation.from_rule),

        Rule('PROTOTYPES', [Expression('not'), RuleRef('PROTOTYPES')],
            Negation.from_rule),

        Rule('VERB_INF', [Expression('not'), RuleRef('VERB_INF')],
            Negation.from_rule)
    }