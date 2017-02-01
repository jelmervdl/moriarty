from typing import Set, Any, Union
from grammar.shared.instance import Instance
from grammar.shared.claim import Claim
import english

class Argument(object):
    """
    An argument exists of claims and attack or support relations between those
    claims, and between the relations themselves.
    """
    def __init__(self, claims: Set[Claim] = {}, relations: Set['Relation'] = {}):
        self.claims = claims
        self.relations = relations

    def __or__(self, other):
        assert isinstance(other, self.__class__)
        return self.__class__(self.claims | other.claims, self.relations | other.relations)

    def __str__(self):
        return " ".join("{!s}.".format(relation) for relation in self.relations)

    def __repr__(self):
        return "Argument(claims={claims!r} relations={relations!r})".format(**self.__dict__)


class Relation(object):
    """
    A relation is an arrow going from one or multiple claims to a claim
    """
    ATTACK = 'attack'
    SUPPORT = 'support'

    def __init__(self, sources: Set[Claim], target: Set[Union[Claim, 'Relation']], type: str):
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
