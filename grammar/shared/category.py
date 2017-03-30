from parser import Rule, State, passthru
from interpretation import Symbol, Interpretation
import english

class Category(object):
    def __init__(self, literal):
        self.literal = literal

    def __hash__(self):
        return hash(self.literal)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.literal == other.literal
    
    def __str__(self):
        return self.literal

    def __repr__(self):
        return "Category({!r})".format(self.literal)

    @property
    def singular(self):
        return self

    @property
    def plural(self):
        return self


class AdjectiveParser(Symbol):
    """
    Adjectives typically and on -ly, -able, -ful, -ical, etc. but you also
    have adjectives such as 'red', 'large', 'rich'. On top of that, you can
    convert verbs to adjectives using -ed and -able. So we'll just accept
    anything today :)
    """
    def test(self, literal: str, position: int, state: State) -> bool:
        return literal not in ('no','not')

    def finish(self, literal: str, state: State):
        return Interpretation(local=Category(literal))


grammar = {
    Rule("CATEGORY", [AdjectiveParser()], passthru)
}
