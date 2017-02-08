from grammar.shared import instance, prototype, category
from parser import Rule, RuleRef, passthru, Literal
from argumentation import Argument
from interpretation import Interpretation
from grammar.utilities import Sequence


class Claim(object):
    """
    Represents claims such as 'Cats are cool' or 'Tweety can fly'. The verb
    is often (always?) a modal verb.
    """

    counter = Sequence()

    def __init__(self, subject, verb, object):
        self.id = self.counter.next()
        self.subject = subject
        self.verb = verb
        self.object = object

    def __repr__(self):
        return "{type}(subject={subject!r}, verb={verb!r}, object={object!r})".format(
            subject=self.subject, verb=self.verb, object=self.object, type=self.__class__.__name__)

    def __str__(self):
        return "{subject!s} {verb!s} {object!s}".format(**self.__dict__)

    def is_same(self, other: 'Claim', argument: Argument) -> bool:
        if self.verb != other.verb:
            return False
        
        if isinstance(self.subject, instance.Instance) and isinstance(other.subject, instance.Instance):
            if not self.subject.is_same(other.subject, argument):
                return False
        elif self.subject != other.subject:
            return False

        if isinstance(self.object, instance.Instance) and isinstance(other.object, instance.Instance):
            if not self.object.is_same(other.object, argument):
                return False
        elif self.object != other.object:
            return False

        return True

    def text(self, argument: Argument) -> str:
        return "{subject!s} {verb!s} {object!s}".format(
            subject=self.subject.text(argument) if 'text' in dir(self.subject) else str(self.subject),
            verb=self.verb,
            object=self.object.text(argument) if 'text' in dir(self.object) else str(self.object))

    @classmethod
    def from_rule(cls, state, data):
        claim = cls(data[0].local, data[1].local, data[2].local)
        return data[0] + data[1] + data[2] + Interpretation(argument=Argument(claims={claim: {claim}}), local=claim)


# grammar = instance.grammar | prototype.grammar | category.grammar | {
#     Rule('SUBJECT', [RuleRef('INSTANCE')], passthru),
#     Rule('SUBJECT', [RuleRef('PROTOTYPE')], passthru),
#     Rule('SUBJECTS', [RuleRef('INSTANCES')], passthru),
#     Rule('SUBJECTS', [RuleRef('PROTOTYPES')], passthru),

#     Rule('CLAIM', [RuleRef('SUBJECT'), Literal('is'), RuleRef('CATEGORY')],
#         Claim.from_rule),

#     Rule('CLAIM', [RuleRef('SUBJECT'), Literal('is'), RuleRef('PROTOTYPE')],
#         Claim.from_rule),

#     Rule('CLAIM', [RuleRef('SUBJECTS'), Literal('are'), RuleRef('CATEGORY')],
#         Claim.from_rule),

#     Rule('CLAIM', [RuleRef('SUBJECTS'), Literal('are'), RuleRef('PROTOTYPES')],
#         Claim.from_rule),

#     # This allows the grammar to use GENERAL and SPECIFIC claims, but behave
#     # as if the distinction is not made, until the actual GENERAL and SPECIFIC
#     # rules are loaded. 
#     Rule('GENERAL_CLAIM', [RuleRef('CLAIM')], passthru),

#     Rule('SPECIFIC_CLAIM', [RuleRef('CLAIM')], passthru)
# }
