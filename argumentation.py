from typing import Set, Any, Union, Dict
from collections import OrderedDict
import english
import parser

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
        return self.__class__(claims, self.relations | other.relations, instances)

    def __str__(self) -> str:
        """Return the argument as (parsable?) English sentences."""
        return " ".join("{!s}.".format(relation) for relation in self.relations)

    def __repr__(self) -> str:
        """Return a string representation of the argument for inspection."""
        return "Argument(claims={claims!r} relations={relations!r})".format(**self.__dict__)

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
        claims = OrderedDict(self.claims)

        for other_claim, other_occurrences in other.claims.items():
            merged = False
            for claim in claims.keys():
                if claim.is_same(other_claim, context):
                    claims[claim] |= other_occurrences
                    merged = True
                    break
            if not merged:
                claims[other_claim] = other_occurrences
        return claims

    def __find_occurrence(self, instances, instance):
        for full_instance, occurrences in instances.items():
            if instance in occurrences:
                return full_instance
        raise ArgumentError('instance not part of this argument')


class Relation(object):
    """
    A relation is an arrow going from one or multiple claims to a claim
    """
    ATTACK = 'attack'
    SUPPORT = 'support'

    def __init__(self, sources: Set['Claim'], target: Set[Union['Claim', 'Relation']], type: str):
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

