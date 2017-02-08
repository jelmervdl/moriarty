from typing import Any, Dict, Set
from argumentation import Argument
import parser


class Interpretation(object):
    def __init__(self, argument: Argument = Argument(), local: Any = None):
        self.argument = argument
        self.local = local

    def __add__(self, other: 'Interpretation') -> 'Interpretation':
        return Interpretation(
            argument = self.argument | other.argument,
            local = other.local)

    def __str__(self) -> str:
        return str(self.argument)

    def __repr__(self) -> str:
        return "Interpretation(argument={argument!r} local={local!r})".format(**self.__dict__)
    


class Symbol(parser.Symbol):
    def finish(self, literal: str, state: parser.State):
        return Interpretation(local=literal)


class Literal(parser.Literal):
    def finish(self, literal: str, state: parser.State):
        return Interpretation(local=literal)
