from parser import parse_syntax, parse_rule, Parser, Symbol, ParseError, indent, flatten
import re
import copy

def newline(text):
    return "\n" + text if text else ""

class ArgumentativeDiscourseUnit:
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

    def as_tuple(self):
        return {
            "adu": str(self),
            "supports": list(map(lambda el: el.as_tuple(), self.supports)),
            "attacks": list(map(lambda el: el.as_tuple(), self.attacks))
        }


class Statement(ArgumentativeDiscourseUnit):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __str__(self):
        return "{}({})".format(self.b, self.a)

    def __repr__(self):
        return "{}{}".format(str(self), newline(indent(super().__repr__(), "|\t")))


class CanStatement(Statement):
    def __str__(self):
        return "{} can {}".format(self.a, self.b)


class IsStatement(Statement):
    def __str__(self):
        return "{} is a {}".format(self.a, self.b)


class HasStatement(Statement):
    def __str__(self):
        return "{} has {}".format(self.a, self.b)


class RuleStatement(Statement):
    def isInstance(self, statement):
        return False


class CanRuleStatement(CanStatement, RuleStatement):
    def isInstance(self, statement):
        return isinstance(statement, CanStatement) and statement.b == self.b


class HasRuleStatement(HasStatement, RuleStatement):
    def isInstance(self, statement):
        return isinstance(statement, HasStatement) and statement.b == self.b


def attack(statement, attack):
        state_copy = copy.deepcopy(statement)
        state_copy.attacks.append(attack)
        return state_copy

def support(statement, support):
        state_copy = copy.deepcopy(statement)
        state_copy.supports.append(support)
        return state_copy

class Negation(ArgumentativeDiscourseUnit):
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


class Combination(ArgumentativeDiscourseUnit):
    def __init__(self, statements):
        self.statements = statements

    def as_tuple(self):
        return {**super().as_tuple(), "statements": list(map(lambda stmt: stmt.as_tuple(), self.statements))}

    def __str__(self):
        return " ⋀ ".join(map(str, self.statements))

    def __repr__(self):
        return "AND (\n{}\n)".format(indent("\n".join(map(repr, self.statements)), ".\t"))

    @property
    def supports(self):
        return flatten(map(lambda stmt: stmt.supports, self.statements))

    @property
    def attacks(self):
        return flatten(map(lambda stmt: stmt.attacks, self.statements))


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
    ("IS ::= TYPES are TYPES", lambda data, n: IsRuleStatement(data[0], data[2])),
    ("HAS ::= INSTANCE has TYPES", lambda data, n: HasStatement(data[0], data[2])),
    ("TYPE ::= a NOUN", lambda data, n: data[1]),
    ("TYPES ::= NOUNS", lambda data, n: data[0]),
    ("CAN ::= INSTANCE can VERB", lambda data, n: CanStatement(data[0], data[2])),
    ("CAN ::= TYPES can VERB", lambda data, n: CanRuleStatement(data[0], data[2])),
    ("CANNOT ::= INSTANCE can not VERB", lambda data, n: Negation(CanStatement(data[0], data[3]))),
    ("CANNOT ::= TYPES can not VERB", lambda data, n: Negation(CanRuleStatement(data[0], data[3]))),
    ("INSTANCE ::= Henry", passthru),
    ("NOUN ::= bird", passthru),
    ("NOUNS ::= birds", passthru),
    ("NOUN ::= pinguin", passthru),
    ("NOUNS ::= pingiuns", passthru),
    ("NOUN ::= feather", passthru),
    ("NOUNS ::= feathers", passthru),
    ("NOUN ::= wing", passthru),
    ("NOUNS ::= wings", passthru),
    ("VERB ::= fly", passthru),
]

sentences = [
    "Henry is a bird but Henry can not fly because Henry is a pinguin and pingiuns can not fly .",
    "Henry is a bird but Henry can not fly because Henry is a pinguin .",
    "Henry can not fly because Henry is a pinguin .",
    "Henry can fly because Henry is a bird and Henry is not a pinguin .",
    "Henry can fly because Henry is a bird because Henry is a pinguin because Henry has feathers .",
    "Henry can fly because Henry is a bird because Henry has wings .",
    "Henry can fly because Henry is a bird and because Henry has wings .",
    "Henry can fly because Henry is a bird and Henry can fly because Henry has wings .",
]

rules = [parse_rule(expression, callback) for expression, callback in grammar]

start = "START"

Operation = ArgumentativeDiscourseUnit # for compatibility for now

if __name__ == '__main__':
    try:
        sentence = sentences[3]
        parser = Parser(rules, start)
        output = parser.tokenize_and_parse(sentence)
        print(sentence)
        for i, parsing in enumerate(output):
            print("{}: {}".format(i + 1, repr(parsing)))
            print("Summary:")
            print("\n".join(map(str, find_sentences(parsing))))
    except ParseError as e:
        print(repr(e))