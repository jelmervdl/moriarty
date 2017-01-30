from parser import Rule, RuleRef, Literal, Symbol, State, passthru
from grammar.shared import name, pronoun, noun
import english


class Instance(object):
    def __init__(self, name: str = None, noun: str = None, pronoun: str = None, origin: 'Instance' = None):
        self.name = name
        self.noun = noun
        self.pronoun = pronoun
        self.origin = origin
        
    def __str__(self):
        if self.name is not None:
            return self.name
        if self.noun is not None:
            return "the {}".format(self.noun)
        else:
            return "(instance)"

    def __repr__(self):
        return "Instance({})".format(" ".join("{}={!r}".format(k, v) for k,v in self.__dict__.items() if v is not None))

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


class InstanceGroup(object):
    def __init__(self, instances = None, noun = None, pronoun = None):
        self.instances = instances if instances is not None else []
        self.noun = noun
        self.pronoun = pronoun

    def __repr__(self):
        return "InstanceGroup({})".format(" ".join("{}={!r}".format(k, v) for k,v in self.__dict__.items() if v is not None))

    def __str__(self):
        if len(self.instances):
            return english.join(self.instances)
        elif self.noun:
            return "the {}".format(self.noun)
        elif self.pronoun:
            return self.pronoun
        else:
            return "(anonymous group of instances)"

    @classmethod
    def from_pronoun_rule(cls, state, data):
        return cls(pronoun=data[0])

    @classmethod
    def from_names_rule(cls, state, data):
        return cls(instances=[Instance(name=name) for name in data[0]])

    @classmethod
    def from_noun_rule(cls, state, data):
        return cls(noun=data[1]) # 1 because of the 'the' at pos 0.



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
        InstanceGroup.from_pronoun_rule),

    Rule("INSTANCES", [RuleRef("NAMES")],
        InstanceGroup.from_names_rule),

    Rule("INSTANCES", [Literal("the"), RuleRef("NOUNS")],
        InstanceGroup.from_noun_rule),
}

