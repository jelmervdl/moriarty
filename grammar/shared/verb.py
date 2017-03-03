from parser import Rule, Symbol, State, passthru
from typing import Any
from interpretation import Interpretation
import re


class Verb(object):
    def __init__(self, literal: str):
        self.literal = literal

    def __hash__(self):
        return hash(self.literal)

    def __eq__(self, other):
        return self.literal == other.literal

    def __str__(self):
        return self.literal

    def __repr__(self):
        return "Verb({})".format(self.literal)


class VerbParser(Symbol):
    def finish(self, literal: str, state: State) -> Any:
        return Interpretation(local=Verb(literal))


class InfVerbParser(VerbParser):
    def test(self, literal: str, position: int, state: State) -> bool:
        return not re.match(r'^\w+([^e]ed|ing|able)$', literal)


grammar = {
    Rule("VERB_INF", [InfVerbParser()], passthru)
}
