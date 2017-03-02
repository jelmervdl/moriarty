from parser import Rule, RuleRef, Literal
from argumentation import Argument, Relation
from interpretation import Interpretation
from grammar.macros import and_rules


class PartialRelation(object):
    def __init__(self, relation_type, specifics, general=None):
        assert all(o.__class__.__name__ == 'SpecificClaim' for o in specifics)
        assert general is None or general.__class__.__name__ == 'GeneralClaim'
        self.type = relation_type
        self.specifics = specifics
        self.general = general

    def instantiate(self, claim):
        assert claim.__class__.__name__ == 'SpecificClaim'
        relation = Relation(sources=self.specifics, target=claim, type=self.type)
        argument = Argument(relations={relation})
        if self.general is not None:
            argument = argument | Argument(relations={Relation([self.general], relation, self.type)})
        return Interpretation(argument=argument, local=claim)
        

def expanded_claim(state, data):
    # specific claim; supports; attacks;
    interpretation = data[0]

    # Add the supporting relations (if there is a 'because' clause)
    if data[1].local:
        interpretation += data[1] + data[1].local.instantiate(data[0].local)

    # Add the attacking relations (if there is a 'but' clause)
    if data[2].local:
        interpretation += data[2] + data[2].local.instantiate(data[0].local)

    return interpretation


grammar = and_rules('EXPANDED_CLAIMS', 'EXPANDED_CLAIM', accept_singular=True) \
    | and_rules('EXPANDED_CLAIMS_GF', 'EXPANDED_CLAIM', first_singleton='GENERAL_CLAIM') \
    | and_rules('EXPANDED_CLAIMS_GL', 'EXPANDED_CLAIM', last_singleton='GENERAL_CLAIM') \
    | {
        Rule('ARGUMENT', [RuleRef('SENTENCE')],
            lambda state, data: data[0]),

        Rule('ARGUMENT', [RuleRef('ARGUMENT'), RuleRef('SENTENCE')],
            lambda state, data: data[0] + data[1]),

        
        Rule('SENTENCE', [RuleRef('EXPANDED_CLAIM'), Literal('.')],
            lambda state, data: data[0]),

        Rule('EXPANDED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), RuleRef('SUPPORT'), RuleRef('ATTACK')],
            expanded_claim),

        Rule('SUPPORT', [Literal('because'), RuleRef('EXPANDED_CLAIMS')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.SUPPORT, specifics=data[1].local))),

        Rule('SUPPORT', [],
            lambda state, data: Interpretation()),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_CLAIMS')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.ATTACK, specifics=data[1].local))),

        Rule('ATTACK', [],
            lambda state, data: Interpretation()),
    }