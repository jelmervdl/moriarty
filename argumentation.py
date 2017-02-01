from typing import Set, Any, Union
# from grammar.shared.claim import Claim
# from grammar.shared.instance import Instance
import english
import parser

class Argument(object):
    """
    An argument exists of claims and attack or support relations between those
    claims, and between the relations themselves.
    """
    def __init__(self, claims: Set['Claim'] = set(), relations: Set['Relation'] = set(), instances: Set['Instance'] = set()):
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
        
        instances = set(self.instances)

        for other_instance in other.instances:
            for existing_instance in instances:
                if other_instance.is_same(existing_instance):
                    print("Instance already in list")
                    found = True
                    break

                if existing_instance.could_be(other_instance):
                    instances.remove(existing_instance)
                    instances.add(existing_instance.replace(other_instance))
                    found = True
                    break

        return self.__class__(self.claims | other.claims, self.relations | other.relations, instances)

    def __str__(self):
        """Return the argument as (parsable?) English sentences."""
        return " ".join("{!s}.".format(relation) for relation in self.relations)

    def __repr__(self):
        """Return a string representation of the argument for inspection."""
        return "Argument(claims={claims!r} relations={relations!r} instances={instances!r})".format(**self.__dict__)


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

