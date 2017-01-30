import re
from parser import Rule, Symbol, State, passthru
import english


class NounParser(Symbol):
    def __init__(self, is_plural):
        self.is_plural = is_plural

    def test(self, literal: str, position: int, state: 'State') -> bool:
        if not literal.islower() and position != 0:
            return False
        if self.is_plural and literal[-1] != 's':
            return False
        if not self.is_plural and literal[-1] == 's':
            return False
        return True

    def finish(self, literal: str, state: 'State'):
        return Noun(literal, self.is_plural)


class Noun(object):
    def __init__(self, literal: str, is_plural: bool):
        self.literal = literal
        self.is_plural = is_plural

    @property
    def singular(self) -> str:
        word = self.literal
        if self.is_plural:
            word = english.singularize(word)
        return word

    @property
    def plural(self) -> str:
        word = self.literal
        if not self.is_plural:
            word = english.pluralize(word)
        return word

    @property
    def is_singular(self) -> bool:
        return not self.is_plural

    def is_same(self, other):
        return self.singular == other.singular

    def __str__(self):
        return self.literal

    def __repr__(self):
        return "Noun({}{})".format(self.literal, ", plural" if self.is_plural else "")


grammar = {
    Rule("NOUN", [NounParser(is_plural=False)], passthru),
    Rule("NOUNS", [NounParser(is_plural=True)], passthru)
}