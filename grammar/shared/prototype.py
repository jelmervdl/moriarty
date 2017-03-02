from parser import Rule, RuleRef, Literal, passthru
from grammar.shared import noun
from english import indefinite_article
from interpretation import Interpretation

class Prototype(object):
    def __init__(self, noun):
        self.noun = noun

    def __hash__(self):
        return hash(self.noun)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.noun == other.noun
    
    def __str__(self):
        if self.noun.is_singular:
            return "{} {}".format(indefinite_article(self.noun.literal), self.noun.literal)
        else:
            return str(self.noun.plural)

    def __repr__(self):
        return "Prototype({!r})".format(self.noun)

    @property
    def singular(self):
        return self.__class__(self.noun.singular)

    @property
    def plural(self):
        return self.__class__(self.noun.plural)


grammar = noun.grammar | {
    Rule("PROTOTYPE", [Literal("a"), RuleRef("NOUN")],
        lambda state, data: data[1] + Interpretation(local=Prototype(data[1].local))),

    Rule("PROTOTYPES", [RuleRef("NOUNS")],
        lambda state, data: data[0] + Interpretation(local=Prototype(data[0].local)))
}