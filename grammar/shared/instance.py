from parser import Rule, RuleRef, State, passthru
from grammar.shared import name, pronoun, noun
from argumentation import Argument
from interpretation import Interpretation, Literal, Expression
from datastructures import Sequence
import english

counter = Sequence()


class Instance(object):
    def __init__(self, name: str = None, noun: str = None, pronoun: str = None, origin: 'Instance' = None, scope: 'Scope' = None):
        self.id = counter.next()
        self.name = name
        self.noun = noun
        self.pronoun = pronoun
        self.origin = origin
        self.scope = scope

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id
        
    def __str__(self):
        if self.name is not None:
            return "{} (#{})".format(self.name, self.id)
        elif self.noun is not None:
            return "the {} (#{})".format(self.noun, self.id)
        elif self.pronoun is not None:
            return "{} (#{})".format(self.pronoun, self.id)
        else:
            return "#{}".format(self.id)

    def __repr__(self):
        return "Instance(id={id!r} name={name!r} noun={noun!r} pronoun={pronoun!r} scope={scope!r})".format(**self.__dict__)

    @property
    def grammatical_number(self):
        return 'singular'

    def text(self, argument: Argument):
        return argument.get_instance(self).__str__()

    def is_same(self, other: 'Instance', argument: Argument) -> bool:
        return argument.get_instance(self) == argument.get_instance(other)

    def could_be(self, other: 'Instance') -> bool:
        if isinstance(other, InstanceGroup):
            return False
        elif self.scope != other.scope:
            return False
        elif self.pronoun == 'something':
            return other.pronoun == 'it'
        elif self.pronoun == 'someone':
            return other.pronoun in ('he', 'she')
        elif self.name is not None:
            return self.name == other.name \
                or other.name is None \
                and (self.pronoun is None and other.pronoun in ('he', 'she') \
                    or self.pronoun == other.pronoun)
        elif self.noun is not None:
            return self.noun == other.noun \
                or other.noun is None and other.pronoun in ('he', 'she', 'it')
        elif self.pronoun == 'it':
            return other.pronoun == 'it'
        elif self.pronoun in ('he', 'she'):
            return self.pronoun == other.pronoun
        else:
            # assert False, "this instance is weird: {!r}".format(self)
            return False

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
        return data[0] + Interpretation(argument=Argument(instances={instance: {instance}}), local=instance)

    @classmethod
    def from_name_rule(cls, state, data):
        instance = cls(name=data[0].local)
        return data[0] + Interpretation(argument=Argument(instances={instance: {instance}}), local=instance)

    @classmethod
    def from_noun_rule(cls, state, data):
        instance = cls(noun=data[1].local) # because 'the'
        return data[1] + Interpretation(argument=Argument(instances={instance: {instance}}), local=instance)


class InstanceGroup(object):
    def __init__(self, instances = None, noun = None, pronoun = None, scope: 'Scope' = None):
        assert instances is None or len(instances) > 1, "A group of one"
        self.id = counter.next()
        self.instances = instances
        self.noun = noun
        self.pronoun = pronoun
        self.scope = scope

    def __repr__(self):
        return "InstanceGroup(id={id!r} instances={instances!r} noun={noun!r} pronoun={pronoun!r} scope={scope!r})".format(**self.__dict__)

    def __str__(self):
        if self.instances:
            return "{} (#{})".format(english.join(self.instances), self.id)
        elif self.noun:
            return "the {} (#{})".format(self.noun.plural, self.id)
        elif self.pronoun:
            return "{} (#{})".format(self.pronoun, self.id)
        else:
            return "(anonymous group of instances #{})".format(self.id)

    @property
    def grammatical_number(self):
        return 'plural'

    def is_same(self, other: 'Instance', argument: Argument) -> bool:
        return argument.get_instance(self) == argument.get_instance(other)

    def could_be(self, other: 'Instance') -> bool:
        if not isinstance(other, self.__class__):
            return False
        elif self.scope != other.scope:
            return False
        elif self.pronoun == 'all':
            return other.pronoun == 'they'
        elif self.instances:
            if other.instances:
                return all(any(instance.could_be(other_instance) for other_instance in other.instances) for instance in self.instances)
            else:
                return other.pronoun in ('they',)
        elif self.noun:
            return self.noun == other.noun \
                or other.noun is None and other.pronoun in ('they',)
        elif self.pronoun:
            return self.pronoun == other.pronoun
        else:
            return False

    @classmethod
    def from_pronoun_rule(cls, state, data):
        instance = cls(pronoun=data[0].local)
        return data[0] + Interpretation(local=instance, argument=Argument(instances={instance: {instance}}))

    @classmethod
    def from_names_rule(cls, state, data):
        instances = {Instance(name=name) for name in data[0].local}
        instance=cls(instances=instances)
        return data[0] + Interpretation(local=instance, argument=Argument(instances={instance: {instance}}))

    @classmethod
    def from_noun_rule(cls, state, data):
        instance = cls(noun=data[1].local)  # 1 because of the 'the' at pos 0.
        return data[1] + Interpretation(local=instance, argument=Argument(instances={instance: {instance}}))


grammar = name.grammar | noun.grammar | pronoun.grammar | {
    # Singular
    Rule("INSTANCE", [RuleRef("PRONOUN")],
        Instance.from_pronoun_rule),

    Rule("INSTANCE", [RuleRef("NAME")],
        Instance.from_name_rule),

    Rule("INSTANCE", [Expression(r"[Tt]he"), RuleRef("NOUN")],
        Instance.from_noun_rule),

    Rule("INSTANCE", [Expression(r"[Hh]is|[Hh]er|[Tt]heir"), RuleRef("NOUN")],
        Instance.from_noun_rule),

    # Plural
    Rule("INSTANCES", [RuleRef("PRONOUNS")],
        InstanceGroup.from_pronoun_rule),

    Rule("INSTANCES", [RuleRef("NAMES")],
        InstanceGroup.from_names_rule),

    Rule("INSTANCES", [Expression(r"[Tt]he"), RuleRef("NOUNS")],
        InstanceGroup.from_noun_rule),

    Rule("INSTANCES", [Expression(r"[Hh]is|[Hh]er|[Tt]heir"), RuleRef("NOUNS")],
        InstanceGroup.from_noun_rule),
}

