from parser import parse_syntax, parse_rule, Parser, Symbol, ParseError, indent, flatten
import re
import copy

def newline(text):
    return "\n" + text if text else ""

class Sentence:
    def __init__(self):
        self.supports = []
        self.attacks = []

    def __repr__(self):
        lines = []
        if self.supports:
            lines.append("Supporting:")
            lines.extend(map(repr, self.supports))
        if self.attacks:
            lines.append("Attacking:")
            lines.extend(map(repr, self.attacks))
        return "\n".join(lines)

class Statement(Sentence):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __str__(self):
        return "{}({})".format(self.b, self.a)

    def __repr__(self):
        return "{}".format(str(self), newline(indent(super().__repr__(), "|\t")))


class CanStatement(Statement):
    def __str__(self):
        return "{} can {}".format(self.a, self.b)


class IsStatement(Statement):
    def __str__(self):
        return "{} is a {}".format(self.a, self.b)


class HasStatement(Statement):
    def __str__(self):
        return "{} has {}".format(self.a, self.b)


def attack(statement, attack):
        state_copy = copy.deepcopy(statement)
        state_copy.attacks.append(attack)
        return state_copy

def support(statement, support):
        state_copy = copy.deepcopy(statement)
        state_copy.supports.append(support)
        return state_copy

class Negation(Sentence):
    def __init__(self, statement):
        self.statement = statement

    def __str__(self):
        return "¬{}".format(str(self.statement))

    def __repr__(self):
        return "¬{}".format(repr(self.statement))

    @property
    def supports(self):
        return self.statement.supports

    @property
    def attacks(self):
        return self.statement.attacks


class Combination(Sentence):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements

    def __str__(self):
        return " ⋀ ".join(map(str, self.statements))

    def __repr__(self):
        return "AND (\n{}\n)".format(indent("\n".join(map(repr, self.statements)), ".\t"))


def find_sentences(parse):
    if isinstance(parse, Combination):
        sentences = parse.statements[:]
    else:
        sentences = [parse]

    sentences.extend(flatten(map(find_sentences,parse.attacks)))
    sentences.extend(flatten(map(find_sentences,parse.supports)))
    return sentences



def passthru(data, n):
    return data[0]

grammar = [
    ("START ::= S .", passthru),
    ("S ::= IS", passthru),
    ("S ::= CAN", passthru),
    ("S ::= CANNOT", passthru),
    ("S ::= HAS", passthru),
    ("S ::= S but S", lambda data, n: attack(data[0], data[2])),
    ("S ::= S because S", lambda data, n: support(data[0], data[2])),
    ("S ::= S and S", lambda data, n: Combination([data[0], data[2]])),
    ("IS ::= INSTANCE is TYPE", lambda data, n: IsStatement(data[0], data[2])),
    ("IS ::= INSTANCE is not TYPE", lambda data, n: Negation(IsStatement(data[0], data[3]))),
    ("IS ::= TYPES are TYPES", lambda data, n: IsStatement(data[0], data[2])),
    ("HAS ::= INSTANCE has TYPES", lambda data, n: HasStatement(data[0], data[2])),
    ("TYPE ::= a NOUN", lambda data, n: data[1]),
    ("TYPES ::= NOUNS", lambda data, n: data[0]),
    ("CAN ::= INSTANCE can VERB", lambda data, n: CanStatement(data[0], data[2])),
    ("CAN ::= TYPES can VERB", lambda data, n: CanStatement(data[0], data[2])),
    ("CANNOT ::= INSTANCE can not VERB", lambda data, n: Negation(CanStatement(data[0], data[3]))),
    ("CANNOT ::= TYPES can not VERB", lambda data, n: Negation(CanStatement(data[0], data[3]))),
    ("INSTANCE ::= Henry", passthru),
    ("NOUN ::= bird", passthru),
    ("NOUNS ::= birds", passthru),
    ("NOUN ::= pinguin", passthru),
    ("NOUNS ::= pingiuns", passthru),
    ("NOUN ::= feather", passthru),
    ("NOUNS ::= feathers", passthru),
    ("VERB ::= fly", passthru),
]

sentences = [
    "Henry is a bird but Henry can not fly because Henry is a pinguin and pingiuns can not fly .",
    "Henry is a bird but Henry can not fly because Henry is a pinguin .",
    "Henry can not fly because Henry is a pinguin .",
    "Henry can fly because Henry is a bird and Henry is not a pinguin .",
    "Henry can fly because Henry is a bird because Henry is a pinguin because Henry has feathers ."
]

if __name__ == '__main__':
    try:
        sentence = sentences[3]

        rules = [parse_rule(expression, callback) for expression, callback in grammar]
        parser = Parser(rules, "START")
        output = parser.tokenize_and_parse(sentence)
        print(sentence)
        for i, parsing in enumerate(output):
            print("{}: {}".format(i + 1, repr(parsing)))
            print("Summary:")
            print("\n".join(map(str, find_sentences(parsing))))
    except ParseError as e:
        print(repr(e))