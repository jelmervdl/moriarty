from typing import Optional

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


class Noun(parser.Symbol):
    def __init__(self, count: str = 'both') -> None:
        if count in ('singular', 'plural', 'both'):
            self.count = count
        else:
            raise ValueError('Count argument should be "singular", "plural" or "both".')

    def test(self, literal:str) ->bool:
        if self.count == 'plural':
            return literal.endswith('s')
        else:
            return True


def singular(word:str) -> str:
    word = re.sub('(e?s)$', '', word)  # Strip 'es' from thieves
    word = re.sub('v$', 'f', word)  # Replace 'v' in 'thiev' with 'f'
    return word


class Operation:
    def as_tuple(self):
        raise NotImplementedError()


class Assertion(Operation):
    def __init__(self, sentence):
        self.sentence = sentence

    def __repr__(self):
        return "ASSERT THAT {}".format(repr(self.sentence))

    def as_tuple(self):
        return 'assertion', self.sentence


class Because(Operation):
    def __init__(self, reason, statement):
        self.reason = reason
        self.statement = statement

    def __repr__(self):
        return "{} BECAUSE {}".format(repr(self.statement), repr(self.reason))

    def as_tuple(self):
        return 'because', self.reason, self.statement


class Rule(Operation):
    def __init__(self, condition, consequence):
        self.condition = condition
        self.consequence = consequence

    def __repr__(self):
        return "IF {} THEN {}".format(repr(self.condition), repr(self.consequence))

    def as_tuple(self):
        return 'rule', self.condition, self.consequence

start = 'ARGSET'

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
        lambda m, n: Assertion((m[0], 'is', m[2]))),

    parser.Rule('STATEMENT',
        [R('PREDICATE'), L('is'), R('PREDICATE')],
        lambda m, n: Rule(m[0], m[2])),

    parser.Rule('STATEMENT',
        [R('PREDICATE'), L('are'), R('PREDICATE')],
        lambda m, n: Rule(m[0], m[2])),

    parser.Rule('ACTOR',
        [Name()],
        lambda m, n: ('person', m[0])),

    parser.Rule('PREDICATE',
        [Adjective()],
        lambda m, n: ('pred', m[0])),
    parser.Rule('PREDICATE',
        [L('a'), Noun('singular')],
        lambda m, n: ('predicate', m[1])),
    parser.Rule('PREDICATE',
        [Noun('plural')],
        lambda m, n: ('predicate', singular(m[0]))),
]