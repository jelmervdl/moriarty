from typing import Set
from parser import Rule, RuleRef, Literal
from grammar.shared.claim import Claim, Scope
from grammar.shared.instance import Instance
from grammar.shared.specific import SpecificClaim
from grammar.shared.prototype import Prototype
from grammar.shared import pronoun, category, prototype, verb, specific
from grammar.macros import and_rules
from argumentation import Argument, Relation
from interpretation import Expression, Interpretation
import english


class ConditionalClaim(Claim):
    """
    An Undetermined Claim is in many ways similar to a specific Claim
    except that the subject is undetermined. It functions as an unbound
    variable, often with the word "something" or "someone".
    """
    def __init__(self, subject, verb, object, conditions = set(), **kwargs):
        super().__init__(subject, verb, object, **kwargs)
        self.conditions = conditions

    def is_preferred_over(self, other: Claim, argument: Argument) -> bool:
        assert isinstance(other, self.__class__)
        return len(self.conditions) > len(other.conditions)

    def text(self, argument: Argument) -> str:
        # Special condition: something can fly if it is a bird -> birds can fly
        # if len(self.conditions) == 1:
        #     (condition,) = self.conditions
        #     if self.subject == condition.subject \
        #         and condition.verb == 'is' \
        #         and isinstance(condition.object, Prototype):
        #         return "{a!s} {verb!s} {b!s}".format(a=condition.object, verb=self.verb, b=self.object)

        return "{} if {}".format(
            super().text(argument),
            english.join([claim.text(argument) for claim in self.conditions]))

    @classmethod
    def from_claim(cls, claim: 'SpecificClaim', conditions: Set['SpecificClaim'], scope: 'Scope') -> 'ConditionalClaim':
        return claim.clone(cls=cls, conditions=conditions, scope=scope)


def undetermined_claim(state, data):
    scope = Scope()
    conditions = set(claim.clone(scope=scope) for claim in data[2].local)
    claim = ConditionalClaim.from_claim(data[0].local, conditions=conditions, scope=scope)
    relation = Relation(conditions, claim, Relation.CONDITION)
    return data[0] + data[2] + Interpretation(
        argument=Argument(
            claims={
                claim: {claim}, 
                **{condition: {condition} for condition in conditions}
            },
            relations={relation}
        ),
        local=claim)


def general_claim(state, data):
    scope = Scope()
    something = Instance(pronoun='something')
    condition = SpecificClaim(something, 'is', data[0].local.singular, scope=scope)
    claim = ConditionalClaim(something, data[1].local, data[2].local, conditions={condition}, scope=scope)
    relation = Relation({condition}, claim, Relation.CONDITION)
    return Interpretation(argument=Argument(claims={claim: {claim}, condition: {condition}}, relations={relation}, instances={something: {something}}), local=claim)


grammar = pronoun.grammar \
    | category.grammar \
    | prototype.grammar \
    | verb.grammar \
    | specific.grammar \
    | and_rules('SPECIFIC_CLAIMS', 'SPECIFIC_CLAIM', accept_singular=True) \
    | {
        # x is an A when x is a B
        Rule('CONDITIONAL_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Expression('if|when'), RuleRef('SPECIFIC_CLAIMS')],
            undetermined_claim),

        # an A is a B
        Rule('CONDITIONAL_CLAIM', [RuleRef('PROTOTYPE'), Expression('is|has'), RuleRef('CATEGORY')],
            general_claim),
        Rule('CONDITIONAL_CLAIM', [RuleRef('PROTOTYPE'), Expression('is|has'), RuleRef('PROTOTYPE')],
            general_claim),

        Rule('CONDITIONAL_CLAIM', [RuleRef('PROTOTYPE'), Expression('can|may|should'), RuleRef('VERB_INF')],
            general_claim),

        # A's are B's
        Rule('CONDITIONAL_CLAIM', [RuleRef('PROTOTYPES'), Expression('are|have'), RuleRef('CATEGORY')],
            general_claim),
        Rule('CONDITIONAL_CLAIM', [RuleRef('PROTOTYPES'), Expression('are|have'), RuleRef('PROTOTYPES')],
            general_claim),

        Rule('CONDITIONAL_CLAIM', [RuleRef('PROTOTYPES'), Expression('can|may|should'), RuleRef('VERB_INF')],
            general_claim),
    }