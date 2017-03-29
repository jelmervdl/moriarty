from parser import Rule, Symbol, State, passthru
from interpretation import Interpretation
import re


class Verb(object):
    def __init__(self, literal: str):
        self.literal = literal

    def __hash__(self):
        return hash(self.literal)

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
            and self.literal == other.literal

    def __str__(self):
        return self.literal

    def __repr__(self):
        return "Verb({})".format(self.literal)

    def for_subject(self, subject):
        if self.literal in ('are', 'is'):
            if subject.grammatical_number is 'plural':
                return Verb('are')
            else:
                return Verb('is')
        elif self.literal in ('have', 'has'):
            if subject.grammatical_number is 'plural':
                return Verb('have')
            else:
                return Verb('has')
        else:
            return self


class VerbParser(Symbol):
    def __init__(self, expression: str, negate: bool = False) -> None:
        self.expression = re.compile(expression)
        self.negate = negate

    def test(self, literal: str, position: int, state: State) -> bool:
        is_match = self.expression.match(literal) is not None
        return is_match is not self.negate

    def __repr__(self) -> str:
        return "/{}/".format(self.expression.pattern)

    def finish(self, literal: str, state: State):
        return Interpretation(local=Verb(literal))


grammar = {
    Rule("VERB_INF", [VerbParser(r'^\w+([^e]ed|ing|able)$', negate=True)], passthru)
}
