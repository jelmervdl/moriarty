from grammar.shared import category, prototype, verb
from grammar.shared.claim import Claim
from parser import Rule, RuleRef, Literal


class GeneralClaim(Claim):
    """
    A general claim is a bit of a rule statement, such as "cats are cool" which
    can be interpreted as if an individual is a cat, it is cool.
    """
    def __init__(self, subject, verb, object):
        assert isinstance(subject, prototype.Prototype), "Subject of a general claim is not a prototype?"
        super().__init__(subject, verb, object)


grammar = category.grammar | prototype.grammar | verb.grammar | {
    # Singular
    Rule('GENERAL_CLAIM', [RuleRef('PROTOTYPE'), Literal('is'), RuleRef('CATEGORY')],
        GeneralClaim.from_rule),
    Rule('GENERAL_CLAIM', [RuleRef('PROTOTYPE'), Literal('is'), RuleRef('PROTOTYPE')],
        GeneralClaim.from_rule),

    # Plural
    Rule('GENERAL_CLAIM', [RuleRef('PROTOTYPES'), Literal('are'), RuleRef('CATEGORY')],
        GeneralClaim.from_rule),
    Rule('GENERAL_CLAIM', [RuleRef('PROTOTYPES'), Literal('are'), RuleRef('PROTOTYPES')],
        GeneralClaim.from_rule),
    Rule('GENERAL_CLAIM', [RuleRef('PROTOTYPES'), Literal('can'), RuleRef('VERB_INF')],
        GeneralClaim.from_rule),
}