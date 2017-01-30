from parser import Rule, RuleRef, Literal, Symbol, State, passthru
from grammar.shared import name, pronoun, noun

class Instance(object):
    def __init__(self, name: str = None, noun: str = None, pronoun: str = None, plural = False, origin: 'Instance' = None):
        self.name = name
        self.noun = noun
        self.pronoun = pronoun
        self.plural = plural
        self.origin = origin
        
    def __str__(self):
        if self.name is not None:
            return self.name
        if self.noun is not None:
            return "the {}".format(self.noun)
        else:
            return "(instance)"

    def __repr__(self):
        return "Instance({})".format(" ".join("{}={}".format(k, v) for k,v in self.__dict__.items() if v is not None))

    def is_same(self, other):
        are_same_individuals = self.replaces(other) or other.replaces(self)
        print("Comparing {!r} and {!r}: {!r}".format(self, other, are_same_individuals))
        return are_same_individuals

    def replaces(self, instance: 'Instance') -> bool:
        """
        Test whether this instance is an updated version of the supplied instance.
        :param instance: the supposed origin of this instance
        :return: whether this instance is a more accurate version of the supplied instance
        """
        previous = self.origin
        while previous is not None:
            if previous == instance:
                return True
            previous = previous.origin
        return False

    def update(self, name: str = None, noun: str = None, pronoun: str = None) -> 'Instance':
        return Instance(
            name=name if name is not None else self.name,
            noun=noun if noun is not None else self.noun,
            pronoun=pronoun if pronoun is not None else self.pronoun,
            origin=self)

grammar = name.grammar | noun.grammar | pronoun.grammar | {
    # Singular
    Rule("INSTANCE", [RuleRef("PRONOUN")],
        lambda state, data: Instance(pronoun=data[0])),

    Rule("INSTANCE", [RuleRef("NAME")],
        lambda state, data: Instance(name=data[0])),

    Rule("INSTANCE", [Literal("the"), RuleRef("NOUN")],
        lambda state, data: Instance(noun=data[1])),

    # Plural
    Rule("INSTANCES", [RuleRef("PRONOUNS")],
        lambda state, data: Instance(pronoun=data[0], plural=True)),

    Rule("INSTANCES", [RuleRef("NAMES")],
        lambda state, data: Instance(name=data[0], plural=True)), # note that data[0] is a list

    Rule("INSTANCES", [Literal("the"), RuleRef("NOUNS")],
        lambda state, data: Instance(noun=data[1], plural=True))
}

