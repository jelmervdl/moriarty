from parser import Rule, RuleRef, Literal, passthru
from grammar.shared import noun
from english import indefinite_article


class Prototype(object):
    def __init__(self, noun):
        self.noun = noun
        
    def __str__(self):
        if self.noun.is_singular:
            return "{} {}".format(indefinite_article(self.noun.literal), self.noun.literal)
        else:
            return self.noun.plural

    def __repr__(self):
        return "Prototype({!r})".format(self.noun)


grammar = noun.grammar | {
    Rule("PROTOTYPE", [Literal("a"), RuleRef("NOUN")],
        lambda state, data: Prototype(data[1])),

    Rule("PROTOTYPES", [RuleRef("NOUNS")],
        lambda state, data: Prototype(data[0]))
}