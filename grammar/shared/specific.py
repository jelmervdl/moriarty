from grammar.shared import instance, category, prototype, verb
from grammar.shared.claim import Claim
from parser import Rule, RuleRef, Literal


class SpecificClaim(Claim):
    """
    A specific claim is a claim that always has an instance as its subject. E.g.
    it is always about 'the' something instead of 'a' something, or a name, or
    a 'they'.
    """
    def __init__(self, subject, verb, object):
        assert isinstance(subject, instance.Instance), "Subject of a specific claim is not an instance?"
        super().__init__(subject, verb, object)


grammar = instance.grammar | category.grammar | prototype.grammar | verb.grammar | {
    Rule('SPECIFIC_CLAIM', [RuleRef('INSTANCE'), Literal('is'), RuleRef('CATEGORY')],
        SpecificClaim.from_rule),
    Rule('SPECIFIC_CLAIM', [RuleRef('INSTANCE'), Literal('is'), RuleRef('PROTOTYPE')],
        SpecificClaim.from_rule),

    Rule('SPECIFIC_CLAIM', [RuleRef('INSTANCES'), Literal('are'), RuleRef('CATEGORY')],
        SpecificClaim.from_rule),
    Rule('SPECIFIC_CLAIM', [RuleRef('INSTANCES'), Literal('are'), RuleRef('PROTOTYPE')],
        SpecificClaim.from_rule),

    Rule('SPECIFIC_CLAIM', [RuleRef('INSTANCE'), Literal('can'), RuleRef('VERB_INF')],
        SpecificClaim.from_rule),

    Rule('SPECIFIC_CLAIM', [RuleRef('INSTANCES'), Literal('can'), RuleRef('VERB_INF')],
        SpecificClaim.from_rule)
}