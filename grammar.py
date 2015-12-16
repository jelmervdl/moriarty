import parser
import re


def L(value: str):
    return parser.Literal(value)


def R(name: str):
    return parser.RuleRef(name)


class Name(parser.Symbol):
    pattern = re.compile(r'^[A-Z][a-z]+$')

    def test(self, literal: str) -> bool:
        return self.pattern.match(literal)


class Adjective(parser.Symbol):
    def test(self, literal:str) -> bool:
        return literal.endswith("able")


class Because:
    def __init__(self, reason, statement):
        self.reason = reason
        self.statement = statement

    def __repr__(self):
        return "{} because {}".format(self.statement, self.reason)

rules = [
    parser.Rule('ARGSET',
        [R('STATEMENT'), L('and'), R('STATEMENT'), L('.')],
        lambda m, n: [m[0], m[2]]),

    parser.Rule('ARGSET',
        [R('STATEMENT'), L('.')],
        lambda m, n: [m[0]]),

    parser.Rule('STATEMENT',
        [R('STATEMENT'), L('because'), R('STATEMENT')],
        lambda m, n: Because(m[2], m[0])),

    parser.Rule('STATEMENT',
        [R('ACTOR'), L('is'), R('PREDICATE')],
        lambda m, n: ('Instantiated Rule', m[0], 'is', m[2])),

    parser.Rule('STATEMENT',
        [R('PREDICATE'), L('is'), R('PREDICATE')],
        lambda m, n: ('Rule', m[0], 'is', m[2])),

    parser.Rule('STATEMENT',
        [R('PREDICATE'), L('are'), R('PREDICATE')],
        lambda m, n: ('Rule', m[0], 'is', m[2])),

    parser.Rule('ACTOR',
        [Name()],
        lambda m, n: ('person', m[0])),

    parser.Rule('PREDICATE',
        [Adjective()],
        lambda m, n: ('pred', m[0])),
    parser.Rule('PREDICATE',
        [L('a'), L('thief')],
        lambda m, n: ('thief',)),
    parser.Rule('PREDICATE',
        [L('thieves')],
        lambda m, n: ('thief',)),
]