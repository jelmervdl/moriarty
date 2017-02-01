from parser import Rule, RuleRef, Literal, passthru
from grammar.shared import noun
from english import indefinite_article
from interpretation import Interpretation

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
        lambda state, data: data[1] + Interpretation(local=Prototype(data[1].local))),

    Rule("PROTOTYPES", [RuleRef("NOUNS")],
        lambda state, data: data[0] + Interpretation(local=Prototype(data[0].local)))
}