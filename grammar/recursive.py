from parser import Rule, RuleRef, Literal
from argumentation import Argument, Relation
from interpretation import Interpretation
from grammar.macros import and_rules


def _relation(relation_type, claim, specifics, general=None):
    relation = Relation(specifics, claim, relation_type)
    argument = Argument(relations={relation})
    if general is not None:
        argument = argument | Argument(relations={Relation([general], relation, relation_type)})
    return argument


def expanded_claim(state, data):
    # specific claim; supports; attacks;
    interpretation = data[0] + data[1] + data[2]

    # Add the supporting relations (if there is a 'because' clause)
    if data[1].local:
        interpretation += Interpretation(argument=_relation(Relation.SUPPORT, data[0].local, specifics=data[1].local))

    # Add the attacking relations (if there is a 'but' clause)
    if data[2].local:
        interpretation += Interpretation(argument=_relation(Relation.ATTACK, data[0].local, specifics=data[2].local))

    # and don't forget to set local back to the specific claim we're augmenting.
    return interpretation + Interpretation(local=data[0].local)


grammar = and_rules('EXPANDED_CLAIMS', 'EXPANDED_CLAIM', accept_singular=True) \
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
            lambda state, data: data[1] + Interpretation(local=data[1].local)),

        Rule('SUPPORT', [],
            lambda state, data: Interpretation(local={})),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_CLAIMS')],
            lambda state, data: data[1] + Interpretation(local=data[1].local)),

        Rule('ATTACK', [],
            lambda state, data: Interpretation(local={})),
    }