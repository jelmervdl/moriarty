from parser import Rule, RuleRef, State, passthru
from interpretation import Literal, Symbol, Interpretation
from grammar.macros import and_rules


class NameParser(Symbol):
    def test(self, literal: str, position: int, state: State) -> bool:
        return literal[0].isupper()


grammar = and_rules('NAMES', 'NAME', accept_singular=False) \
    | { Rule("NAME", [NameParser()], passthru) }