from parser import Rule, RuleRef, Literal
from argumentation import Argument, Relation
from interpretation import Interpretation
from grammar.macros import and_rules


def support(claim, specifics, general=None):
    relation = Relation(specifics, claim, Relation.SUPPORT)
    argument = Argument(relations={relation})
    if general is not None:
        argument = argument | Argument(relations={Relation([general], relation, Relation.SUPPORT)})
    return argument


def attack(claim, specifics):
    relation = Relation(specifics, claim, Relation.ATTACK)
    argument = Argument(relations={relation})
    return argument


grammar = and_rules('EXPANDED_CLAIMS', 'EXPANDED_CLAIM') \
    | {
        Rule('ARGUMENT', [RuleRef('SENTENCE')],
            lambda state, data: data[0]),

        Rule('ARGUMENT', [RuleRef('ARGUMENT'), RuleRef('SENTENCE')],
            lambda state, data: data[0] + data[1]),

        
        Rule('SENTENCE', [RuleRef('EXPANDED_CLAIM'), Literal('.')],
            lambda state, data: data[0]),

        Rule('EXPANDED_CLAIM', [RuleRef('SPECIFIC_CLAIM')],
            lambda state, data: data[0]),

        Rule('EXPANDED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('EXPANDED_CLAIM')],
            lambda state, data: data[0] + data[2] + Interpretation(argument=support(data[0].local, specifics={data[2].local}))),

        Rule('EXPANDED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('EXPANDED_CLAIMS')],
            lambda state, data: data[0] + data[2] + Interpretation(argument=support(data[0].local, specifics=data[2].local))),



        # Rule('ATTACKED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('but'), RuleRef('SPECIFIC_CLAIM')],
        #     lambda state, data: data[0] + data[2] + Interpretation(argument=attack(data[0].local, specifics={data[2].local}))),

        # Rule('ATTACKED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('but'), RuleRef('SPECIFIC_CLAIMS')],
        #     lambda state, data: data[0] + data[2] + Interpretation(argument=attack(data[0].local, specifics=data[2].local))),


        # Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('GENERAL_CLAIM'), Literal('and'), RuleRef('SPECIFIC_CLAIM')],
        #     lambda state, data: data[0] + data[2] + data[4] + Interpretation(argument=support(data[0].local, general=data[2].local, specifics={data[4].local}))),
        
        # Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('GENERAL_CLAIM'), Literal(','), RuleRef('SPECIFIC_CLAIMS')],
        #     lambda state, data: data[0] + data[2] + data[4] + Interpretation(argument=support(data[0].local, general=data[2].local, specifics=data[4].local)))
    }