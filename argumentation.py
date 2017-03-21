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

        assert all(instance.__class__.__name__ == 'Instance' for instance in instances)

        self.claims = claims
        self.relations = relations
        self.instances = instances

        # Assert all the sources in a relation are claims, and all of them are in our claims set
        # assert all(claim in self.claims for relation in self.relations for claim in relation.sources)

        # Assert all the targets relations point to are in our claims set (if they point to a claim instead of a relation)
        # assert all(relation.target in self.claims for relation in self.relations if isinstance(relation.target, Claim))

    def __or__(self, other):
        """Combine two Arguments into one."""
        assert isinstance(other, self.__class__)
        instances = self.__merge_instances(other)
        claims = self.__merge_claims(other, self.__class__(instances=instances))
        relations = self.__merge_relations(other)

        for claim in self.claims.keys():
            assert self.__find_occurrence(claims, claim)

        for claim in other.claims.keys():
            assert self.__find_occurrence(claims, claim)

        argument = self.__class__(claims, relations, instances)
        
        # for a in new_claims:
        #     for b in claims.keys():
        #         if a.scope == b.scope \
        #             and a.object.__class__.__name__ == 'Negation' \
        #             and a.subject.__class__.__name__ == 'Instance' \
        #             and b.subject.__class__.__name__ == 'Instance' \
        #             and argument.find_instance(a.subject) == argument.find_instance(b.subject) \
        #             and a.verb == b.verb \
        #             and a.object.object == b.object:
        #             argument.relations.add(Relation(sources={a}, target=b, type=Relation.ATTACK))

        return argument


    def __str__(self) -> str:
        """Return the argument as (parsable?) English sentences."""
        return " ".join("{!s}.".format(relation) for relation in self.relations)

    def __repr__(self) -> str:
        """Return a string representation of the argument for inspection."""
        return "Argument(claims={claims!r} relations={relations!r})".format(**self.__dict__)

    def with_scope(self, scope: 'Scope') -> 'Argument':
        claims = OrderedDict()
        for claim, occurrences in self.claims.items():
            scoped_claim = claim.clone(scope=scope)
            claims[scoped_claim] = {scoped_claim} | occurrences
        return self.__class__(claims, self.relations, self.instances)

    def find_claim(self, claim: 'Claim') -> 'Claim':
        return self.__find_occurrence(self.claims, claim)

    def find_instance(self, instance: 'Instance') -> 'Instance':
        return self.__find_occurrence(self.instances, instance)

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
        raise RuntimeError('Instance {!r} not part of this argument'.format(instance))


class Relation(object):
    """
    A relation is an arrow going from one or multiple claims to a claim
    """
    ATTACK = 'attack'
    SUPPORT = 'support'
    CONDITION = 'condition'

    def __init__(self, sources: Set['Claim'], target: Union['Claim', 'Relation'], type: str):
        from grammar.shared.claim import Claim
        
        assert all(isinstance(o, Claim) for o in sources)
        assert isinstance(target, Claim) or isinstance(target, Relation)
        assert type in (self.ATTACK, self.SUPPORT, self.CONDITION)

        self.sources = sources
        self.target = target
        self.type = type

    def __str__(self):
        return "{target!s} {conj} {sources}".format(
            target=self.target,
            conj='because' if self.type == self.SUPPORT else 'except',
            sources=english.join(self.sources))

    def __repr__(self):
        return "Relation(sources={sources!r} target={target!r} type={type!r})".format(**self.__dict__)

