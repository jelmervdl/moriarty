from parser import Rule, RuleRef, Literal
from argumentation import Argument
from interpretation import Interpretation, Expression
from grammar.shared.conditional import ConditionalClaim
from grammar.shared.specific import SpecificClaim
from grammar.shared.instance import Instance
from grammar import recursive


class SpecificBlob(SpecificClaim):
    def __init__(self, subject, verb, object, literals, **kwargs):
        self.literals = literals
        super().__init__(subject, verb, object, **kwargs)

    def clone(self, cls=None, **kwargs):
        kwargs['literals'] = self.literals
        return super().clone(cls, **kwargs)

    def text(self, argument):
        return " ".join(self.literals)


class ConditionalBlob(ConditionalClaim):
    def __init__(self, subject, verb, object, literals, **kwargs):
        self.literals = literals
        super().__init__(subject, verb, object, **kwargs)

    def clone(self, cls=None, **kwargs):
        kwargs['literals'] = self.literals
        return super().clone(cls, **kwargs)

    def text(self, argument):
        return " ".join(self.literals)


def blob_specific_claim(state, data):
    subject = Instance()
    verb = None
    object = None
    claim = SpecificBlob(subject, verb, object, data[0])
    argument = Argument(instances={subject: {subject}}, claims={claim: {claim}})
    return Interpretation(argument=argument, local=claim)


def blob_conditional_claim(state, data):
    subject = Instance()
    verb = None
    object = None
    claim = ConditionalBlob(subject, verb, object, data[0])
    argument = Argument(instances={subject: {subject}}, claims={claim: {claim}})
    return Interpretation(argument=argument, local=claim)


grammar = recursive.grammar | {
    Rule('SPECIFIC_CLAIM', [RuleRef('BLOB')], blob_specific_claim),
    
    Rule('CONDITIONAL_CLAIM', [RuleRef('BLOB')], blob_conditional_claim),

    Rule('BLOB_WORD', [Expression(r'(?!because|but)')],
        lambda state, data: data[0].local),
    
    Rule('BLOB', [RuleRef('BLOB_WORD')],
        lambda state, data: [data[0]]),
    
    Rule('BLOB', [RuleRef('BLOB'), RuleRef('BLOB_WORD')],
        lambda state, data: data[0] + [data[1]]),
}