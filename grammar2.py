from parser import parse_syntax, parse_rule, Parser, Rule, Symbol, ParseError, indent, flatten, tokenize
import re
import copy

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

    def __str__(self):
        return "{a} {verb} {b}".format(**self.__dict__)

    def __repr__(self):
        return "{}{}".format(str(self), newline(indent(super().__repr__(), "|\t")))


class CompoundStatement(ArgumentativeDiscourseUnit):
    def __init__(self, constituents):
        super().__init__()
        self.constituents = constituents
    
    def __str__(self):
        return " AND ".join(map(str, self.constituents))

    def as_tuple(self):
        return {**super().as_tuple(), 'type': 'compound', 'sources': list(source.as_tuple() for source in self.constituents)}


class Arrow(ArgumentativeDiscourseUnit):
    def __init__(self, source):
        super().__init__()
        if isinstance(source, Arrow):
            self.source = source.source
            self.arrows = source.arrows
        else:
            self.source = source

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
        self.statement = statement

    def __str__(self):
        return "¬{}".format(str(self.statement))

    def __repr__(self):
        return "¬{}".format(repr(self.statement))

    @property
    def arrows(self):
        return self.statement.arrows


def find_sentences(parse):
    sentences = [parse]
    sentences.extend(flatten(map(find_sentences,parse.arrows)))
    return sentences


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


def passthru(data, n):
    return data[0]

def noop(data, n):
    return 'empty'

grammar = [
    ("START ::= S .", passthru),
    ("S ::= INST", passthru),
    ("S ::= RULE", passthru),
    ("S ::= S but S", lambda data, n: attack(data[0], data[2])),
    ("S ::= S because S", lambda data, n: support(data[0], data[2])),
    ("S ::= S because S and because S", lambda data, n: support(data[0], data[2], data[5])),
    ("S ::= INST and RULE", lambda data, n: ruleinstance(data[2], data[0])),
    ("S ::= RULE and INST", lambda data, n: ruleinstance(data[0], data[2])),
    ("S ::= INST and INST", lambda data, n: CompoundStatement([data[0], data[2]])),
    ("INST ::= INSTANCE is TYPE", lambda data, n: Statement(data[0], "is", data[2])),
    ("INST ::= INSTANCE is VERB_ABLE", lambda data, n: Statement(data[0], "is", data[2])),
    ("INST ::= INSTANCE is VERB_ING", lambda data, n: Statement(data[0], "is", data[2])),
    ("INST ::= INSTANCE is not TYPE", lambda data, n: Negation(Statement(data[0], "is", data[3]))),
    ("INST ::= INSTANCE has TYPES", lambda data, n: Statement(data[0], "has", data[2])),
    ("TYPE ::= a NOUN", lambda data, n: data[1]),
    ("TYPE ::= an NOUN", lambda data, n: data[1]),
    ("TYPES ::= NOUNS", lambda data, n: data[0]),
    ("INST ::= INSTANCE can VERB_INF", lambda data, n: Statement(data[0], "can", data[2])),
    ("RULE ::= TYPES are TYPES", lambda data, n: Statement(data[0], "are", data[2])),
    ("RULE ::= TYPES are VERB_ABLE", lambda data, n: Statement(data[0], "are", data[2])),
    ("RULE ::= TYPES are VERB_ING", lambda data, n: Statement(data[0], "are", data[2])),
    ("RULE ::= TYPES can VERB_INF", lambda data, n: Statement(data[0], "can", data[2])),
    ("RULE ::= TYPES have TYPES", lambda data, n: Statement(data[0], "have", data[2])),
    ("INST ::= INSTANCE can not VERB_INF", lambda data, n: Negation(Statement(data[0], "can", data[3]))),
    ("RULE ::= TYPES can not VERB_INF", lambda data, n: Negation(Statement(data[0], "can", data[3]))),
    ("INSTANCE ::= NAME", passthru),
    ("INSTANCE ::= he", passthru),
    ("INSTANCE ::= she", passthru)
]

sentences = [
    "Henry can fly.",
    "Henry can fly because he is a bird.",
    "Henry can fly because he is a bird and birds can fly.",
    "Henry can fly because birds can fly and he is a bird.",
    "Henry can fly because he is a bird and because he has wings.",
    "Henry can fly because he has wings but he is not a bird.",
    "Henry can fly because he is a bird and he has wings.",
    "Henry can fly because he is a bird and he has wings because birds have wings and he is a bird."
    # "Henry is a bird but Henry can not fly because Henry is a pinguin and pingiuns can not fly .",
    # "Henry is a bird but Henry can not fly because Henry is a pinguin .",
    # "Henry can not fly because Henry is a pinguin .",
    # "Henry can fly because Henry is a bird and Henry is not a pinguin .",
    # "Henry can fly because Henry is a bird because Henry is a pinguin because Henry has feathers .",
    # "Henry can fly because Henry is a bird because Henry has wings .",
    # "Henry can fly because Henry is a bird and because Henry has wings .",
    # "Henry can fly because Henry is a bird and Henry can fly because Henry has wings .",
]

class Noun(Symbol):
    def __init__(self, plural):
        self.plural = plural

    def test(self, literal: str, position: int) -> bool:
        if not literal.islower() and position != 0:
            return False
        if self.plural and literal[-1] != 's':
            return False
        return True

    def singular(self, literal: str) -> str:
        word = re.sub('(e?s)$', '', word)  # Strip 'es' from thieves
        word = re.sub('v$', 'f', word)  # Replace 'v' in 'thiev' with 'f'
        return word


class Name(Symbol):
    def test(self, literal: str, position: int) -> bool:
        return literal[0].isupper()


class ReSymbol(Symbol):
    def __init__(self, pattern: str, negate=False) -> None:
        self.pattern = re.compile(pattern)
        self.negate = negate

    def test(self, literal:str, position:int) -> bool:
        accept = re.match(self.pattern, literal) is not None
        return not accept if self.negate else accept


rules = list(parse_rule(expression, callback) for expression, callback in grammar)

rules += [
    Rule("NOUN", [Noun(plural=False)], passthru),
    Rule("NOUNS", [Noun(plural=True)], passthru),
    Rule("NAME", [Name()], passthru),
    Rule("VERB_INF", [ReSymbol(r'^\w+([^e]ed|ing|able)$', negate=True)], passthru),
    Rule("VERB_ING", [ReSymbol(r'^\w+ing$')], passthru),
    Rule("VERB_ABLE", [ReSymbol(r'^\w+able$')], passthru),
]

start = "START"

Operation = ArgumentativeDiscourseUnit # for compatibility for now

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