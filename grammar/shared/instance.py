from parser import Rule, RuleRef, Literal, Symbol, State, passthru
from grammar.shared import name, pronoun, noun
from argumentation import Argument
from interpretation import Interpretation
import english


class Sequence(object):
    def __init__(self):
        self.value = 0

    def next(self):
        self.value += 1
        return self.value


class Instance(object):
    counter = Sequence()

    def __init__(self, name: str = None, noun: str = None, pronoun: str = None, origin: 'Instance' = None):
        self.id = self.counter.next()
        self.name = name
        self.noun = noun
        self.pronoun = pronoun
        self.origin = origin
        
    def __str__(self):
        if self.name is not None:
            identifier = self.name
        elif self.noun is not None:
            identifier = "the {}".format(self.noun)
        elif self.pronoun is not None:
            identifier = self.pronoun
        return "{} (#{})".format(identifier, self.id)

    def __repr__(self):
        return "Instance(id={id!r} name={name!r} noun={noun!r} pronoun={pronoun!r})".format(**self.__dict__)

    def is_same(self, other: 'Instance') -> bool:
        return self.replaces(other) or other.replaces(self)

    def could_be(self, other: 'Instance') -> bool:
        if self.name is not None and other.name is not None:
            return self.name == other.name
        elif self.noun is not None and other.noun is not None:
            return self.noun == other.noun
        elif self.pronoun is not None and other.pronoun is not None:
            return self.pronoun == other.pronoun
        else:
            return True

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

    def replace(self, other: 'Instance') -> 'Instance':
        return self.update(other.name, other.noun, other.pronoun)

    def update(self, name: str = None, noun: str = None, pronoun: str = None) -> 'Instance':
        return Instance(
            name=name if name is not None else self.name,
            noun=noun if noun is not None else self.noun,
            pronoun=pronoun if pronoun is not None else self.pronoun,
            origin=self)

    @classmethod
    def from_pronoun_rule(cls, state, data):
        instance = cls(pronoun=data[0].local)
        return data[0] + Interpretation(Argument(instances={instance}), instance)

    @classmethod
    def from_name_rule(cls, state, data):
        instance = cls(name=data[0].local)
        return data[0] + Interpretation(Argument(instances={instance}), instance)

    @classmethod
    def from_noun_rule(cls, state, data):
        instance = cls(noun=data[1].local) # because 'the'
        return data[1] + Interpretation(Argument(instances={instance}), instance)

    


class InstanceGroup(object):
    def __init__(self, instances = None, noun = None, pronoun = None):
        self.instances = instances if instances is not None else {}
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
        instance = cls(pronoun=data[0].local)
        return data[0] + Interpretation(local=instance)

    @classmethod
    def from_names_rule(cls, state, data):
        instances = {Instance(name=name) for name in data[0].local}
        return data[0] + Interpretation(Argument(instances=instances), cls(instances=instances))

    @classmethod
    def from_noun_rule(cls, state, data):
        return data[1] + Interpretation(local=cls(noun=data[1].local)) # 1 because of the 'the' at pos 0.



grammar = name.grammar | noun.grammar | pronoun.grammar | {
    # Singular
    Rule("INSTANCE", [RuleRef("PRONOUN")],
        Instance.from_pronoun_rule),

    Rule("INSTANCE", [RuleRef("NAME")],
        Instance.from_name_rule),

    Rule("INSTANCE", [Literal("the"), RuleRef("NOUN")],
        Instance.from_noun_rule),

    # Plural
    Rule("INSTANCES", [RuleRef("PRONOUNS")],
        InstanceGroup.from_pronoun_rule),

    Rule("INSTANCES", [RuleRef("NAMES")],
        InstanceGroup.from_names_rule),

    Rule("INSTANCES", [Literal("the"), RuleRef("NOUNS")],
        InstanceGroup.from_noun_rule),
}

