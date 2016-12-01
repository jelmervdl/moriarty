import itertools

from parser import parse_syntax, parse_rule, read_sentences, Parser, Rule, State, Symbol, ParseError, indent, flatten, tokenize
from typing import List, Optional, Any, Callable, Union, cast, Set, Dict
from collections import OrderedDict
import re
import copy
import debug
import os.path


logger = debug.Console()


def newline(text):
    return "\n" + text if text else ""


class ArgumentativeDiscourseUnit:
    def __init__(self):
        self.arrows = []

    def __repr__(self):
        lines = []
        if self.arrows:
            lines.append("Supporting/Attacking:")
            lines.extend(map(repr, self.arrows))
        return "\n".join(lines)

    def elements(self) -> Set[Any]:
        # Maybe it is unwise to use a set instead of a list here, as the
        # order does matter!
        return set(itertools.chain(*[arrow.elements() for arrow in self.arrows]))

    def as_tuple(self):
        return {
            "type": "adu",
            "text": str(self),
            "args": list(map(lambda el: el.as_tuple(), self.arrows))
        }


class Statement(ArgumentativeDiscourseUnit):
    def __init__(self, a, verb, b):
        super().__init__()
        self.a = a
        self.verb = verb
        self.b = b

    def elements(self):
        return {self.a, self.b} | super().elements()

    def __str__(self):
        return "{a} {verb} {b}".format(**self.__dict__)

    def __repr__(self):
        return "{}{}".format(str(self), newline(indent(super().__repr__(), "|\t")))


class RuleStatement(Statement):
    def __str__(self):
        return "Rule({})".format(super().__str__())

    def is_applicable(self, instances):
        for instance in instances:
            print("  {!r}".format(instance))
        return True


class CompoundStatement(ArgumentativeDiscourseUnit):
    def __init__(self, constituents):
        super().__init__()
        self.constituents = constituents

    def elements(self):
        return set(itertools.chain(*[con.elements() for con in self.constituents])) | super().elements()

    def __str__(self):
        return " AND ".join(map(str, self.constituents))

    def as_tuple(self):
        return {**super().as_tuple(), 'type': 'compound',
                'sources': list(source.as_tuple() for source in self.constituents)}


class Arrow(ArgumentativeDiscourseUnit):
    def __init__(self, source):
        super().__init__()
        if isinstance(source, Arrow):
            self.source = source.source
            self.arrows = source.arrows
        else:
            self.source = source

    def elements(self) -> List[Any]:
        return self.source.elements() | super().elements()

    def __str__(self):
        return "ARROW({})".format(str(self.source))

    def __repr__(self):
        return "{}{}".format(str(self), newline(indent(super().__repr__(), "+\t")))

    def as_tuple(self):
        return {**super().as_tuple(), 'type': 'undefarrow', 'sources': [self.source.as_tuple()]}


class Attack(Arrow):
    def __str__(self):
        return "ATTACK({})".format(self.source)

    def as_tuple(self):
        return {**super().as_tuple(), 'type': 'attack'}


class Support(Arrow):
    def __str__(self):
        return "SUPPORT({})".format(self.source)

    def as_tuple(self):
        return {**super().as_tuple(), 'type': 'support'}


class Negation(ArgumentativeDiscourseUnit):
    def __init__(self, statement):
        #super().__init__() // Don't call super.init since we've overridden the arrows attribute!
        self.statement = statement

    def elements(self):
        return self.statement.elements() | super().elements()

    def __str__(self):
        return "¬{}".format(str(self.statement))

    def __repr__(self):
        return "¬{}".format(repr(self.statement))

    @property
    def arrows(self):
        return self.statement.arrows


def find_sentences(parse):
    return [parse] + flatten(map(find_sentences, parse.arrows))


def attack(statement, attack):
    state_copy = copy.deepcopy(statement)
    state_copy.arrows.append(Attack(attack))
    return state_copy


def support(statement, *args):
    state_copy = copy.deepcopy(statement)
    for support in args:
        state_copy.arrows.append(Support(support))
    return state_copy


def ruleinstance(rule, instance):
    arrow = Arrow(instance)
    arrow.arrows.append(Support(rule))
    return arrow


def passthru(state, data):
    return data[0]


def noop(state, data):
    return 'empty'


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
        return "Instance({})".format(" ".join("{}={}".format(k, v) for k,v in self.__dict__.items() if v is not None))

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


class InstanceList(object):
    @classmethod
    def from_state(cls, state: State) -> 'InstanceList':
        instances = cls()
        for adu in state.data:
            if isinstance(adu, ArgumentativeDiscourseUnit):
                for item in adu.elements():
                    if isinstance(item, Instance) and item not in instances:
                        instances.append(item)
        if state.parent:
            instances.extend(InstanceList.from_state(state.parent))
        return instances

    def __init__(self):
        self.instances = list() # type: List[Instance]

    def __iter__(self):
        return self.instances.__iter__()

    def __len__(self):
        return len(self.instances)

    def append(self, new_instance: Instance):
        for known_instance in self.instances:
            if new_instance.replaces(known_instance):
                self.instances.remove(known_instance)
                break
            if known_instance.replaces(new_instance):
                logger.warn("Trying to add an instance ({!r}) of which already a more specific one ({!r}) is known. "
                            "Ignoring new instance.".format(new_instance, known_instance))
                return
        self.instances.append(new_instance)

    def extend(self, instances: 'InstanceList'):
        for instance in instances:
            self.append(instance)


def find_instance_by_name(state: State, name: str) -> Instance:
    """
    We've received a name, and now we want to link this to an existing instance
    with the same name, or create a new instance.
    :param state:
    :param name:
    :return:
    """
    for instance in InstanceList.from_state(state):
        if instance.name == name:
            return instance
    return Instance(name=name)


def find_instance_by_pronoun(state: State, pronoun: str) -> Instance:
    instances = InstanceList.from_state(state)
    # First of all, we assume the pronoun refers to at least something
    if len(instances) == 0:
        raise Exception("Cannot figure out where '{}' refers to".format(pronoun))
    # Then, we assume that the pronoun refers to the last mentioned instance
    for instance in instances:
        if instance.pronoun == pronoun:
            return instance
        if instance.pronoun is None:
            return instance.update(pronoun=pronoun)


def find_instance_by_noun(state: State, noun: str) -> Instance:
    for instance in InstanceList.from_state(state):
        if instance.noun == noun:
            return instance
    return Instance(noun=noun)


grammar = [
    ("START ::= S .", passthru),
    ("S ::= SPECIFIC", passthru),
    ("S ::= GENERAL", passthru),
    ("S ::= S but S", lambda state, data: attack(data[0], data[2])),
    ("S ::= S because S", lambda state, data: support(data[0], data[2])),
    ("S ::= S because S and because S", lambda state, data: support(data[0], data[2], data[5])),
    ("S ::= SPECIFIC and GENERAL", lambda state, data: ruleinstance(data[2], data[0])),
    ("S ::= GENERAL and SPECIFIC", lambda state, data: ruleinstance(data[0], data[2])),
    ("S ::= SPECIFIC and SPECIFIC", lambda state, data: CompoundStatement([data[0], data[2]])),
    ("SPECIFIC ::= INSTANCE is TYPE", lambda state, data: Statement(data[0], "is", data[2])),
    ("SPECIFIC ::= INSTANCE is VERB_ABLE", lambda state, data: Statement(data[0], "is", data[2])),
    ("SPECIFIC ::= INSTANCE is VERB_ING", lambda state, data: Statement(data[0], "is", data[2])),
    ("SPECIFIC ::= INSTANCE is not TYPE", lambda state, data: Negation(Statement(data[0], "is", data[3]))),
    ("SPECIFIC ::= INSTANCE has TYPES", lambda state, data: Statement(data[0], "has", data[2])),
    ("TYPE ::= a NOUN", lambda state, data: data[1]),
    ("TYPE ::= an NOUN", lambda state, data: data[1]),
    ("TYPES ::= NOUNS", lambda state, data: data[0]),
    ("SPECIFIC ::= INSTANCE can VERB_INF", lambda state, data: Statement(data[0], "can", data[2])),
    ("GENERAL ::= TYPES are TYPES", lambda state, data: RuleStatement(data[0], "are", data[2])),
    ("GENERAL ::= TYPES are VERB_ABLE", lambda state, data: RuleStatement(data[0], "are", data[2])),
    ("GENERAL ::= TYPES are VERB_ING", lambda state, data: RuleStatement(data[0], "are", data[2])),
    ("GENERAL ::= TYPES can VERB_INF", lambda state, data: RuleStatement(data[0], "can", data[2])),
    ("GENERAL ::= TYPES have TYPES", lambda state, data: RuleStatement(data[0], "have", data[2])),
    ("SPECIFIC ::= INSTANCE can not VERB_INF", lambda state, data: Negation(Statement(data[0], "can", data[3]))),
    ("GENERAL ::= TYPES can not VERB_INF", lambda state, data: Negation(Statement(data[0], "can", data[3]))),
    ("INSTANCE ::= NAME", lambda state, data: find_instance_by_name(state, data[0])),
    ("INSTANCE ::= PRONOUN", lambda state, data: find_instance_by_pronoun(state, data[0])),
    ("INSTANCE ::= the NOUN", lambda state, data: find_instance_by_noun(state, data[1]))
]

sentence_files = [os.path.join(os.path.dirname(__file__), 'sentences.txt')]
sentences = OrderedDict()

for sentence_file in sentence_files:
    with open(sentence_file, 'r') as fh:
        sentences.update(read_sentences(fh))


class NounSymbol(Symbol):
    def __init__(self, plural):
        self.plural = plural

    def test(self, literal: str, position: int, state: 'State') -> bool:
        if not literal.islower() and position != 0:
            return False
        if self.plural and literal[-1] != 's':
            return False
        return True

    def singular(self, word: str) -> str:
        word = re.sub('(e?s)$', '', word)  # Strip 'es' from thieves
        word = re.sub('v$', 'f', word)  # Replace 'v' in 'thiev' with 'f'
        return word


class NameSymbol(Symbol):
    def test(self, literal: str, position: int, state: State) -> bool:
        return literal[0].isupper()


class PronounSymbol(Symbol):
    def test(self, literal: str, position: int, state: State) -> bool:
        return literal in ('he', 'she', 'it')


class ReSymbol(Symbol):
    def __init__(self, pattern: str, negate=False) -> None:
        self.pattern = re.compile(pattern)
        self.negate = negate

    def test(self, literal: str, position: int, state: State) -> bool:
        accept = re.match(self.pattern, literal) is not None
        return not accept if self.negate else accept


rules = list(parse_rule(expression, callback) for expression, callback in grammar)

rules += [
    Rule("NOUN", [NounSymbol(plural=False)], passthru),
    Rule("NOUNS", [NounSymbol(plural=True)], passthru),
    Rule("NAME", [NameSymbol()], lambda state, data: data[0]),
    Rule("PRONOUN", [PronounSymbol()], lambda state, data: data[0]),
    Rule("VERB_INF", [ReSymbol(r'^\w+([^e]ed|ing|able)$', negate=True)], passthru),
    Rule("VERB_ING", [ReSymbol(r'^\w+ing$')], passthru),
    Rule("VERB_ABLE", [ReSymbol(r'^\w+able$')], passthru),
]

start = "START"

Operation = ArgumentativeDiscourseUnit  # for compatibility for now

if __name__ == '__main__':
    try:
        for sentence in sentences[:4]:
            parser = Parser(rules, start)
            tokens = tokenize(sentence)
            output = parser.parse(tokens)
            print(sentence)
            for i, parsing in enumerate(output):
                print("{}: {}".format(i + 1, repr(parsing)))
                print("Summary:")
                print("\n".join(map(str, find_sentences(parsing))))
    except ParseError as e:
        print(repr(e))
