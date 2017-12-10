from typing import Set, Any, Union, Dict
from collections import OrderedDict
import english
import parser
from copy import copy

class ArgumentError(Exception):
    pass

class Argument(object):
    """
    An argument exists of claims and attack or support relations between those
    claims, and between the relations themselves.
    """
    def __init__(self,
        claims: Dict['Claim', Set['Claim']] = {},
        relations: Set['Relation'] = set(),
        instances: Dict['Instance', Set['Instance']] = {}):
        
        assert isinstance(claims, dict)
        assert isinstance(relations, set)
        assert isinstance(instances, dict)

        assert all(instance.__class__.__name__ in ('Instance', 'InstanceGroup') for instance in instances)

        self.claims = claims
        self.relations = relations
        self.instances = instances

        # Don't assert whether all instances are already are available, because in some cases this isn't yet true:
        # e.g. when adding a new overall claim, this argument is part of an interpretation that still has to be 
        # merged with other interpretations that carry the information about the instance!
        # for claim in claims.keys():
        #    assert self.__find_occurrence(instances, claim.subject)

        # Assert all the sources in a relation are claims, and all of them are in our claims set
        # assert all(claim in self.claims for relation in self.relations for claim in relation.sources)

        # Assert all the targets relations point to are in our claims set (if they point to a claim instead of a relation)
        # assert all(relation.target in self.claims for relation in self.relations if isinstance(relation.target, Claim))

    def __or__(self, other):
        """Combine two Arguments into one."""
        assert isinstance(other, self.__class__)
        
        instances = self.__merge_instances(other)
        assert len(instances) >= max(len(self.instances), len(other.instances))

        claims = self.__merge_claims(other, self.__class__(instances=instances))
        assert len(claims) >= max(len(self.claims), len(other.claims))
        
        relations = self.__merge_relations(other)

        for claim in self.claims.keys():
            assert self.__find_occurrence(claims, claim) is not None

        for claim in other.claims.keys():
            assert self.__find_occurrence(claims, claim) is not None

        # This assertion does not hold: sometimes we only merge with this information
        # later on
        #for claim in claims.keys():
        #    assert self.__find_occurrence(instances, claim.subject) is not None

        argument = self.__class__(claims, relations, instances)
        
        # If one of the incoming claims is the negation of one of our own claims
        # we need to add an (assumed?) attack relation between the two!
        for a in other.claims:
            a_subj = argument.find_instance(a.subject)
            if a_subj is not None:
                for b in claims.keys():
                    if a.scope == b.scope \
                        and a.object.__class__.__name__ == 'Negation' \
                        and a.subject.__class__.__name__ == 'Instance' \
                        and b.subject.__class__.__name__ == 'Instance' \
                        and a_subj == argument.find_instance(b.subject) \
                        and a.verb == b.verb \
                        and a.object.object == b.object:
                        argument.relations.add(Relation(sources={a}, target=b, type=Relation.ATTACK, assumption=True))
                        argument.relations.add(Relation(sources={b}, target=a, type=Relation.ATTACK, assumption=True))
        
        return argument


    def __str__(self) -> str:
        """Return the argument as (parsable?) English sentences."""
        return " ".join("{!s}.".format(relation) for relation in self.relations)

    def __repr__(self) -> str:
        """Return a string representation of the argument for inspection."""
        return "Argument(claims={claims!r} relations={relations!r} instances={instances!r})".format(**self.__dict__)

    def with_scope(self, scope: 'Scope') -> 'Argument':
        claims = OrderedDict()
        for claim, occurrences in self.claims.items():
            scoped_claim = claim.clone(scope=scope)
            claims[scoped_claim] = {scoped_claim} | occurrences
        return self.__class__(claims, self.relations, self.instances)

    def find_claim(self, claim: 'Claim') -> 'Claim':
        return self.__find_occurrence(self.claims, claim)

    def get_claim(self, claim: 'Claim') -> 'Claim':
        return self.__get_occurrence(self.claims, claim)

    def find_instance(self, instance: 'Instance') -> 'Instance':
        return self.__find_occurrence(self.instances, instance)

    def get_instance(self, instance: 'Instance') -> 'Instance':
        return self.__get_occurrence(self.instances, instance)

    def __merge_instances(self, other: 'Argument') -> Dict['Instance', Set['Instance']]:
        # Merge the instances of this and the other Interpretation
        instances = OrderedDict(self.instances)
        for other_instance, other_occurrences in other.instances.items():
            merged = False

            # Check for all known instances whether they could be the same as
            # the other Interpretation's instance
            for instance in instances.keys():
                # If that is the case, update our instance and add the other's
                # instance to the list of occurrences
                if instance.could_be(other_instance):
                    merged_instance = instance.replace(other_instance)
                    instances[merged_instance] = instances[instance] | {merged_instance} | other_occurrences
                    del instances[instance]
                    merged = True
                    break

            # if it is new, just copy it to our table
            if not merged:
                instances[other_instance] = other_occurrences
        return instances

    def __merge_claims(self, other: 'Argument', context: 'Argument') -> Dict['Claim', Set['Claim']]:
        claims = OrderedDict()
        matched = set()

        for other_claim in other.claims.keys():
            merged = False
            for claim in self.claims.keys():
                if claim.is_same(other_claim, context):
                    key = claim if claim.is_preferred_over(other_claim, context) else other_claim
                    claims[key] = self.claims[claim] | other.claims[other_claim]
                    matched.add(claim)
                    merged = True
                    break
            if not merged:
                claims[other_claim] = other.claims[other_claim]

        for claim in self.claims.keys():
            if claim not in matched:
                claims[claim] = self.claims[claim]

        return claims

    def __merge_relations(self, other: 'Argument') -> Set['Relation']:
        relations = set()
        other_merged = set()

        for relation in self.relations:
            merged = False
            for other_relation in other.relations:
                if relation.target == other_relation.target \
                    and relation.type == other_relation.type \
                    and relation.sources <= other_relation.sources:
                    relations.add(Relation(relation.sources | other_relation.sources, relation.target, relation.type))
                    other_merged.add(other_relation)
                    merged = True
                    break
            if not merged:
                relations.add(relation)

        relations.update(other.relations ^ other_merged)
        return relations

    def __find_occurrence(self, instances, instance):
        assert instance is not None
        for full_instance, occurrences in instances.items():
            if instance in occurrences:
                return full_instance
        return None

    def __get_occurrence(self, instances, instance):
        found = self.__find_occurrence(instances, instance)
        if found is None:
            raise RuntimeError('Instance {!r} not part of this argument'.format(instance))
        return found


class Relation(object):
    """
    A relation is an arrow going from one or multiple claims to a claim
    """
    ATTACK = 'attack'
    SUPPORT = 'support'
    CONDITION = 'condition'

    def __init__(self, sources: Set['Claim'], target: Union['Claim', 'Relation'], type: str, assumption: bool = False):
        from grammar.shared.claim import Claim
        
        assert all(isinstance(o, Claim) for o in sources), 'All relations sources have to be claims'
        assert isinstance(target, Claim) or isinstance(target, Relation), 'Relation target has to be a claim or a relation'
        assert type in (self.ATTACK, self.SUPPORT, self.CONDITION), 'Relation type has to be attack, support or condition'

        self.sources = set(sources)
        self.target = target
        self.type = type
        self.assumption = assumption

    def __str__(self):
        return "{target!s} {conj} {sources}".format(
            target=self.target,
            conj='because' if self.type == self.SUPPORT else 'except',
            sources=english.join(self.sources))

    def __repr__(self):
        return "Relation(sources={sources!r} target={target!r} type={type!r}, assumption={assumption!r})".format(**self.__dict__)

