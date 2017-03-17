from parser import Rule, RuleRef, Literal
from argumentation import Argument, Relation
from interpretation import Interpretation
from grammar.macros import and_rules
from grammar.shared.conditional import ConditionalClaim


class PartialRelation(object):
    def __init__(self, relation_type, specifics, conditional=None):
        # assert all(o.__class__.__name__ == 'SpecificClaim' for o in specifics)
        assert conditional is None or isinstance(conditional, ConditionalClaim)
        self.type = relation_type
        self.specifics = specifics
        self.conditional = conditional

    def instantiate(self, claim):
        # assert claim.__class__.__name__ == 'SpecificClaim'
        relation = Relation(sources=self.specifics, target=claim, type=self.type)
        argument = Argument(relations={relation})
        if self.conditional is not None:
            argument = argument | Argument(relations={Relation([self.conditional], relation, Relation.SUPPORT)})
            # Assume all the conditions for the claim are supported (assumed)
            if len(self.conditional.conditions) > 0:
                assumptions = [condition.assume(subject=claim.subject) for condition in self.conditional.conditions]
                argument = argument | Argument(claims=dict((assumption, {assumption}) for assumption in assumptions))
                for assumption in assumptions:
                    print("Assuming {!r}".format(assumption))
                # relation.sources.extend(assumptions) ## TODO: This breaks everything
                
        return Interpretation(argument=argument, local=claim)
        

def expanded_claim(state, data):
    # specific claim; supports; attacks;
    interpretation = data[0]

    # Add the supporting relations (if there is a 'because' clause)
    if data[1].local:
        interpretation += data[1]
        for support in data[1].local:
            interpretation += support.instantiate(data[0].local)

    # Add the attacking relations (if there is a 'but' clause)
    if data[2].local:
        interpretation += data[2]
        for attack in data[2].local:
            interpretation += attack.instantiate(data[0].local)

    return interpretation


grammar = and_rules('EXPANDED_SPECIFIC_CLAIMS', 'EXPANDED_SPECIFIC_CLAIM', accept_singular=True) \
    | and_rules('EXPANDED_SPECIFIC_CLAIMS_CONDITIONAL_FIRST', 'EXPANDED_SPECIFIC_CLAIM', first_singleton='EXPANDED_CONDITIONAL_CLAIM') \
    | and_rules('EXPANDED_SPECIFIC_CLAIMS_CONDITIONAL_LAST', 'EXPANDED_SPECIFIC_CLAIM', last_singleton='EXPANDED_CONDITIONAL_CLAIM') \
    | and_rules('SUPPORTS', 'SUPPORT', accept_singular=True) \
    | and_rules('ATTACKS', 'ATTACK', accept_singular=True) \
    | {
        Rule('ARGUMENT', [RuleRef('SENTENCE')],
            lambda state, data: data[0]),

        Rule('ARGUMENT', [RuleRef('ARGUMENT'), RuleRef('SENTENCE')],
            lambda state, data: data[0] + data[1]),

        
        Rule('SENTENCE', [RuleRef('EXPANDED_SPECIFIC_CLAIM'), Literal('.')],
            lambda state, data: data[0]),

        Rule('EXPANDED_SPECIFIC_CLAIM', [RuleRef('SPECIFIC_CLAIM'), RuleRef('SUPPORTS'), RuleRef('ATTACKS')],
            expanded_claim),

        Rule('EXPANDED_CONDITIONAL_CLAIM', [RuleRef('CONDITIONAL_CLAIM'), RuleRef('SUPPORTS'), RuleRef('ATTACKS')],
            expanded_claim),

        Rule('SUPPORT', [Literal('because'), RuleRef('EXPANDED_SPECIFIC_CLAIMS')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.SUPPORT, specifics=data[1].local))),

        Rule('SUPPORT', [Literal('because'), RuleRef('EXPANDED_SPECIFIC_CLAIMS_CONDITIONAL_FIRST')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.SUPPORT, conditional=data[1].local[0], specifics=data[1].local[1:]))),

        Rule('SUPPORT', [Literal('because'), RuleRef('EXPANDED_SPECIFIC_CLAIMS_CONDITIONAL_LAST')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.SUPPORT, conditional=data[1].local[-1], specifics=data[1].local[0:-1]))),

        Rule('SUPPORTS', [],
            lambda state, data: Interpretation()),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_SPECIFIC_CLAIMS')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.ATTACK, specifics=data[1].local))),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_SPECIFIC_CLAIMS_CONDITIONAL_FIRST')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.ATTACK, conditional=data[1].local[0], specifics=data[1].local[1:]))),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_SPECIFIC_CLAIMS_CONDITIONAL_LAST')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.ATTACK, conditional=data[1].local[-1], specifics=data[1].local[0:-1]))),

        Rule('ATTACKS', [],
            lambda state, data: Interpretation()),
    }