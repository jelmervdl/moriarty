from parser import Rule, RuleRef, Literal
from argumentation import Argument, Relation
from interpretation import Interpretation
from grammar.macros import and_rules
from grammar.shared.claim import Scope
from grammar.shared.instance import Instance
from grammar.shared.negation import Negation
from grammar.shared.prototype import Prototype
from grammar.shared.conditional import ConditionalClaim, find_conditions


class PartialRelation(object):
    def __init__(self, relation_type, specifics=None, conditional=None):
        # assert all(o.__class__.__name__ == 'SpecificClaim' for o in specifics)
        assert conditional is None or isinstance(conditional, ConditionalClaim)
        self.type = relation_type
        self.specifics = specifics
        self.conditional = conditional

    def instantiate(self, claim, context):
        # assert claim.__class__.__name__ == 'SpecificClaim'
        relation = Relation(sources={}, target=claim, type=self.type)
        argument = Argument(relations={relation})

        if self.specifics is not None:
            relation.sources.update(self.specifics)

        if self.conditional is not None:
            argument = argument | Argument(relations={Relation([self.conditional], relation, Relation.SUPPORT)})
            print("Searching for {!r} in {!r}".format(self.conditional, context))
            conditions = find_conditions(self.conditional, context)
            if len(conditions) > 0:
                assumptions = []
                for condition in conditions:
                    params = {
                        'subject': claim.subject,
                        'verb': condition.verb.for_subject(claim.subject),
                    }

                    if condition.verb.literal in ('is', 'are'):
                        params['object'] = getattr(condition.object, claim.subject.grammatical_number)
                    
                    assumptions.append(condition.assume(**params))

                argument = argument | Argument(claims=dict((assumption, {assumption}) for assumption in assumptions))
                relation.sources.update(assumptions)
        
        if self.conditional is None and self.specifics is not None:
            """
            Make a general assumption in the trend of 'When Tweety can fly
            because she is a bird, anything that is a bird can fly.'
            """
            subject = Instance(pronoun='something')
            
            if self.type == Relation.SUPPORT:
                object = claim.object
            elif self.type == Relation.ATTACK:
                object = Negation(claim.object) #is this ok? Or are we jumping to conclusions?
            else:
                assert False, "Can't deal with this kind of relation"

            conditional = ConditionalClaim(subject, claim.verb, object, scope=Scope(), assumption=True)
            assumptions = []
            
            for specific in self.specifics:
                print("Testing if {!r} could be {!r}".format(claim.subject, specific.subject))
                if claim.subject.could_be(specific.subject):
                    assumptions.append(specific.clone(id=None, subject=conditional.subject, scope=conditional.scope))

            if len(assumptions) > 0:
                print("Adding support {!r} for {!r}".format(conditional, relation))
                argument = argument | Argument(
                    instances={subject: {subject}},
                    claims={conditional: {conditional}, **{assumption: {assumption} for assumption in assumptions}},
                    relations={
                        Relation([conditional], relation, Relation.SUPPORT),
                        Relation(assumptions, conditional, Relation.CONDITION)
                    })
        
        assert len(relation.sources) > 0, "Cannot instantiate relation without specific or assumed claims."

        return Interpretation(argument=argument, local=claim)
        

def expanded_claim(state, data):
    # specific claim; supports; attacks;
    interpretation = data[0]

    # Add the supporting relations (if there is a 'because' clause)
    if data[1].local:
        interpretation += data[1]
        for support in data[1].local:
            interpretation += support.instantiate(data[0].local, data[1].argument)

    # Add the attacking relations (if there is a 'but' clause)
    if data[2].local:
        interpretation += data[2]
        for attack in data[2].local:
            interpretation += attack.instantiate(data[0].local, data[2].argument)

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

        Rule('SUPPORT', [Literal('because'), RuleRef('EXPANDED_CONDITIONAL_CLAIM')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.SUPPORT, conditional=data[1].local))),

        Rule('SUPPORTS', [],
            lambda state, data: Interpretation()),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_SPECIFIC_CLAIMS')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.ATTACK, specifics=data[1].local))),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_SPECIFIC_CLAIMS_CONDITIONAL_FIRST')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.ATTACK, conditional=data[1].local[0], specifics=data[1].local[1:]))),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_SPECIFIC_CLAIMS_CONDITIONAL_LAST')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.ATTACK, conditional=data[1].local[-1], specifics=data[1].local[0:-1]))),

        Rule('ATTACK', [Literal('but'), RuleRef('EXPANDED_CONDITIONAL_CLAIM')],
            lambda state, data: data[1] + Interpretation(local=PartialRelation(Relation.ATTACK, conditional=data[1].local))),

        Rule('ATTACKS', [],
            lambda state, data: Interpretation()),
    }