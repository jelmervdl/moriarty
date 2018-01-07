import re
from grammar.shared import adjective
from parser import Rule, RuleRef, Symbol, passthru
from interpretation import Interpretation
import english


class NounParser(Symbol):
    def __init__(self, is_plural):
        self.is_plural = is_plural

    def test(self, literal: str, position: int, state: 'State') -> bool:
        # Is it a name?
        if not literal.islower() and position != 0: 
            return False

        # Otherwise, delegate the testing to the English library of hacks.
        if self.is_plural:
            return english.is_plural(literal)
        else:
            return english.is_singular(literal)

    def finish(self, literal: str, state: 'State'):
        return Interpretation(local=Noun(literal, self.is_plural))


class Noun(object):
    def __init__(self, literal: str, is_plural: bool, adjectives = []):
        self.literal = literal if not is_plural else english.singularize(literal)
        self.is_plural = is_plural
        self.adjectives = adjectives

    def __hash__(self):
        return hash(self.literal) * 1 if self.is_plural else -1

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
            and self.literal == other.literal \
            and self.is_plural == other.is_plural

    def with_adjective(self, adjective):
        return self.__class__(self.literal, is_plural=self.is_plural, adjectives=[adjective] + self.adjectives)

    @property
    def singular(self) -> 'Noun':
        return self if not self.is_plural else self.__class__(self.literal, is_plural=False, adjectives=self.adjectives)

    @property
    def plural(self) -> 'Noun':
        return self if self.is_plural else self.__class__(self.literal, is_plural=True, adjectives=self.adjectives)

    @property
    def grammatical_number(self) -> str:
        return 'plural' if self.is_plural else 'singular'

    def is_same(self, other):
        return self.literal == other.literal \
            and self.is_plural == other.is_plural

    def __str__(self):
        noun = english.pluralize(self.literal) if self.is_plural else self.literal
        return " ".join(self.adjectives + [noun])

    def __repr__(self):
        return "Noun({}, {})".format(" ".join(self.adjectives + [self.literal]), self.grammatical_number)


grammar = adjective.grammar | {
    Rule("NOUN", [NounParser(is_plural=False)], passthru),
    Rule("NOUNS", [NounParser(is_plural=True)], passthru),
    
    Rule("NOUN", [RuleRef('ADJECTIVE'), NounParser(is_plural=False)],
        lambda state, data: Interpretation(local=data[1].local.with_adjective(data[0].local))),

    Rule("NOUNS", [RuleRef('ADJECTIVE'), NounParser(is_plural=True)],
        lambda state, data: Interpretation(local=data[1].local.with_adjective(data[0].local)))
}