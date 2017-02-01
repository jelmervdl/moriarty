from parser import Rule, RuleRef, Literal
from argumentation import Argument, Relation


def macro_and(name, singleton):
    """
    Creates a mini-grammar of rules that are needed to parse 'A and B',
    'A, B and C', 'A, B, C and D', etc. where A, B, C and D all are parseable
    using the rule name passed using the singleton argument.
    """
    helper = name + "_"
    return {
        # _ and C
        Rule(name, [RuleRef(helper), Literal('and'), RuleRef(singleton)],
            lambda state, data: data[0] | {data[2]}),

        # A, B # (allows for 'A, B and C')
        Rule(helper, [RuleRef(helper), Literal(','), RuleRef(name)],
            lambda state, data: data[0] | {data[2]}),

        # A (allows for 'A and B')
        Rule(helper, [RuleRef(singleton)],
            lambda state, data: {data[0]})
    }


def support(claim, specifics, general=None):
    relation = Relation(specifics, claim, Relation.SUPPORT)
    argument = Argument({claim}, {relation})
    if general is not None:
        argument.relations.add(Relation([general], relation, Relation.SUPPORT))
    return argument


grammar = macro_and('SPECIFIC_CLAIMS', 'SPECIFIC_CLAIM') \
    | {
        Rule('ARGUMENT', [RuleRef('SENTENCE')],
            lambda state, data: data[0]),

        Rule('ARGUMENT', [RuleRef('ARGUMENT'), RuleRef('SENTENCE')],
            lambda state, data: data[0] | data[1]),

        
        Rule('SENTENCE', [RuleRef('SUPPORTED_CLAIM'), Literal('.')],
            lambda state, data: data[0]),

        
        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('SPECIFIC_CLAIM')],
            lambda state, data: support(data[0], specifics={data[2]})),

        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('SPECIFIC_CLAIMS')],
            lambda state, data: support(data[0], specifics=data[2])),

        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('GENERAL_CLAIM'), Literal('and'), RuleRef('SPECIFIC_CLAIM')],
            lambda state, data: support(data[0], general=data[2], specifics={data[4]})),
        
        Rule('SUPPORTED_CLAIM', [RuleRef('SPECIFIC_CLAIM'), Literal('because'), RuleRef('GENERAL_CLAIM'), Literal(','), RuleRef('SPECIFIC_CLAIMS')],
            lambda state, data: support(data[0], general=data[2], specifics=data[4]))
    }