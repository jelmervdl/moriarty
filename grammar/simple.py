from parser import Rule, RuleRef, Literal
from argumentation import Argument, Relation
from interpretation import Interpretation
from grammar.macros import and_rules
from grammar.shared.specific import SpecificClaim


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


def assume(claim, general):
    assumption = SpecificClaim(claim.subject, 'is', general.subject.singular, assumption=True)
    argument = Argument(claims={assumption: {assumption}})
    argument |= support(claim, general=general, specifics={assumption})
    return Interpretation(argument=argument, local=claim)


grammar = and_rules('SPECIFIC_CLAIMS', 'SPECIFIC_CLAIM') \
    | {
        Rule('ARGUMENT', [RuleRef('SENTENCE')],
            lambda state, data: data[0]),

        Rule('ARGUMENT', [RuleRef('ARGUMENT'), RuleRef('SENTENCE')],
            lambda state, data: data[0] + data[1]),

        
        Rule('SENTENCE', [RuleRef('SUPPORTED_CLAIM'), Literal('.')],
            lambda state, data: data[0]),

        Rule('SENTENCE', [RuleRef('ATTACKED_CLAIM'), Literal('.')],
            lambda state, data: data[0]),


        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('SPECIFIC_CLAIM')],
            lambda state, data: data[0] + data[2] + Interpretation(argument=support(data[0].local, specifics={data[2].local}))),

        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('SPECIFIC_CLAIMS')],
            lambda state, data: data[0] + data[2] + Interpretation(argument=support(data[0].local, specifics=data[2].local))),


        Rule('ATTACKED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('but'), RuleRef('SPECIFIC_CLAIM')],
            lambda state, data: data[0] + data[2] + Interpretation(argument=attack(data[0].local, specifics={data[2].local}))),

        Rule('ATTACKED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('but'), RuleRef('SPECIFIC_CLAIMS')],
            lambda state, data: data[0] + data[2] + Interpretation(argument=attack(data[0].local, specifics=data[2].local))),


        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('GENERAL_CLAIM'), Literal('and'), RuleRef('SPECIFIC_CLAIM')],
            lambda state, data: data[0] + data[2] + data[4] + Interpretation(argument=support(data[0].local, general=data[2].local, specifics={data[4].local}))),
        
        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('GENERAL_CLAIM'), Literal(','), RuleRef('SPECIFIC_CLAIMS')],
            lambda state, data: data[0] + data[2] + data[4] + Interpretation(argument=support(data[0].local, general=data[2].local, specifics=data[4].local))),

        # Experimental, don't know if I want this
        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('GENERAL_CLAIM')],
            lambda state, data: data[0] + data[2] + assume(data[0].local, data[2].local))
    }