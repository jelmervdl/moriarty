from typing import Set
from parser import Rule, RuleRef, Literal
from grammar.shared.claim import Claim
from grammar.shared.general import GeneralClaim
from grammar.shared import pronoun, category, prototype, verb, specific
from grammar.macros import and_rules
from argumentation import Argument, Relation
from interpretation import Expression, Interpretation
from copy import copy
import english


class ConditionalClaim(GeneralClaim):
    """
    An Undetermined Claim is in many ways similar to a specific Claim
    except that the subject is undetermined. It functions as an unbound
    variable, often with the word "something" or "someone".
    """
    def __init__(self, subject, verb, object, conditions = set()):
        super(GeneralClaim, self).__init__(subject, verb, object) #skip the checks in GeneralClaim.__init__
        self.conditions = conditions

    def is_preferred_over(self, other: Claim, argument: Argument) -> bool:
        assert isinstance(other, self.__class__)
        return len(self.conditions) > len(other.conditions)

    def text(self, argument: Argument) -> str:
        return "{} if {}".format(
            super().text(argument),
            english.join([claim.text(argument) for claim in self.conditions]))

    @classmethod
    def from_claim(cls, claim: 'SpecificClaim', conditions: Set['SpecificClaim']) -> 'ConditionalClaim':
        expanded = copy(claim)
        expanded.__class__ = cls #brr what an upcast!
        expanded.conditions = conditions
        return expanded


def undetermined_claim(state, data):
    claim = ConditionalClaim.from_claim(data[0].local, conditions=data[2].local)
    relation = Relation(data[2].local, claim, Relation.CONDITION)
    return data[0] + data[2] + Interpretation(argument=Argument(claims={claim: {claim}}, relations={relation}), local=claim)


grammar = pronoun.grammar \
    | category.grammar \
    | prototype.grammar \
    | verb.grammar \
    | specific.grammar \
    | and_rules('SPECIFIC_CLAIMS', 'SPECIFIC_CLAIM', accept_singular=True) \
    | {
        Rule('GENERAL_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Expression('if|when'), RuleRef('SPECIFIC_CLAIMS')],
            undetermined_claim),
    }