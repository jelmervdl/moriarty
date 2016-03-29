#!/usr/bin/env python3

# Based on https://github.com/Hardmath123/nearley/blob/master/lib/nearley.js
import operator
from typing import List, Optional, Any, Callable, Union, cast
import functools
import sys
import re


def log(line: str) -> None:
    pass


def flatten(lists):
    out = []
    for list in lists:
        out.extend(list)
    return out


def indent(text: str, indent: str = "\t"):
    return "\n".join((indent + line for line in text.split("\n"))) if text else ""

class ParseError(Exception):
    def __init__(self, position: int, token: str, sentence: List[str] = None):
        self.position = position
        self.token = token
        self.sentence = sentence
        super().__init__("No possible parse for '{}' (at position {})".format(token, position))

    def __repr__(self) -> str:
        return "{}\n{}\n{}{}{}{}".format(
            super().__repr__(),
            " ".join(self.sentence),
            " " * len(" ".join(self.sentence[0:self.position])),
            " " if self.position > 0 else "",
            "^" * len(self.sentence[self.position]),
            " " * len(" ".join(self.sentence[self.position + 1:])))
        

class RuleParseException(Exception):
    pass




class Symbol:
    def test(self, literal: str, position: int) -> bool:
        raise NotImplementedError("Sybmol.test is abstract")


class Literal(Symbol):
    def __init__(self, literal: str) -> None:
        self.literal = literal

    def test(self, literal: str, position: int) -> bool:
        return self.literal == literal

    def __repr__(self) -> str:
        return "\"{}\"".format(self.literal)


class RuleRef(Symbol):
    def __init__(self, name: str) -> None:
        self.name = name

    def test(self, literal: str, position: int) -> bool:
        return False

    def __repr__(self, with_cursor_at: int = None) -> str:
        return "{}".format(self.name)


class Rule:
    def __init__(self, name: str, symbols: List[Symbol], callback: Optional[Callable[[Any, int], Any]] = None) -> None:
        self.name = name
        self.symbols = symbols
        if callback is not None:
            self.callback = callback
        else:
            self.callback = lambda data, n: RuleInstance(self, data)#flatten(data)

    def __repr__(self, with_cursor_at: int = None) -> str:
        if with_cursor_at is not None:
            return "{} --> {} ● {}".format(
                    self.name,
                    " ".join(map(repr, self.symbols[:with_cursor_at])),
                    " ".join(map(repr, self.symbols[with_cursor_at:])))
        else:
            return "{} --> {}".format(self.name, " ".join(map(repr, self.symbols)))

    def finish(self, data, reference, FAIL) -> Any:
        log("!!! Finishing {} with data {} and reference {}!".format(self.name, data, reference))
        return self.callback(data, reference)


class RuleInstance:
    def __init__(self, rule: Rule, data: List[Any]):
        self.rule = rule
        self.data = data

    def __repr__(self):
        if len(self.data) > 1:
            return "[{}:\n{}\n]".format(self.rule.name, indent("\n".join(map(repr, self.data))))
        elif len(self.data) == 1:
            return "[{}: {}]".format(self.rule.name, repr(self.data[0]))
        else:
            return "[{}: (empty)]".format(self.rule.name)


class State:
    def __init__(self, rule: Rule, expect: int, reference: int) -> None:
        assert len(rule.symbols) > 0
        self.rule = rule
        self.expect = expect
        self.reference = reference
        self.data = [] # type: List[Any]

    def __repr__(self) -> str:
        return "{{}}, from: {}".format(self.rule.__repr__(self.expect), self.reference)

    def nextState(self, data) -> 'State':
        state = State(self.rule, self.expect + 1, self.reference)
        state.data = self.data[:]
        state.data.append(data)
        return state

    def consumeTerminal(self, inp: str, token_pos: int) -> Optional['State']:
        log("consumeTerminal {} using {} expecting {}".format(inp, self.rule, self.rule.symbols[self.expect] if len(
            self.rule.symbols) > self.expect else '>END<'))
        if len(self.rule.symbols) > self.expect and self.rule.symbols[self.expect].test(inp, position=token_pos):
            log("Terminal consumed")
            return self.nextState(inp)
        else:
            return None

    def consumeNonTerminal(self, inp: Rule) -> Optional['State']:
        assert isinstance(inp, Rule)
        if len(self.rule.symbols) > self.expect \
            and isinstance(self.rule.symbols[self.expect], RuleRef) \
            and self.rule.symbols[self.expect].name == inp.name:
            return self.nextState(inp)
        else:
            return None

    def process(self, location, table: List[List['State']], rules: List[Rule], added_rules: List[Rule]) -> None:
        if self.expect == len(self.rule.symbols):
            # We have a completed rule
            try:
                self.data = self.rule.finish(self.data, self.reference, Parser.FAIL)

                w = 0
                # We need a while here because the empty rule will modify table[reference] when location == reference
                while w < len(table[self.reference]):
                    state = table[self.reference][w]
                    next = state.consumeNonTerminal(self.rule)
                    if next is not None:
                        next.data[-1] = self.data
                        table[location].append(next)
                    w += 1

                    # --- The comment below is OUTDATED. It's left so that future
                    # editors know not to try and do that.

                    # Remove this rule from "addedRules" so that another one can be
                    # added if some future added rule requires it.
                    # Note: I can be optimized by someone clever and not-lazy. Somehow
                    # queue rules so that everything that this completion "spawns" can
                    # affect the rest of the rules yet-to-be-added-to-the-table.
                    # Maybe.

                    # I repeat, this is a *bad* idea.

                    # var i = addedRules.indexOf(this.rule);
                    # if (i !== -1) {
                    #     addedRules.splice(i, 1);
                    # }
            except ParseError:
                log("apparently {} could not be parsed here".format(self.rule))
                pass
        else:
            # in case I missed an older nullable's sweep, update yourself. See
            # above context for why this makes sense
            ind = table[location].index(self)
            for i in range(ind):
                state = table[location][i]
                if len(state.rule.symbols) == state.expect and state.reference == location:
                    x = self.consumeNonTerminal(state.rule)
                    if x is not None:
                        x.data[-1] = state.data
                        table[location].append(x)

            # I'm not done, but I can predict something
            expected_symbol = self.rule.symbols[self.expect]

            if isinstance(expected_symbol, RuleRef):
                for rule in rules:
                    if rule.name == expected_symbol.name and rule not in added_rules:
                        # Make a note that you've added it already, and don't need to
                        # add it again; otherwise left recursive rules are going to go
                        # into an infinite loop by adding themselves over and over
                        # again.

                        # If it's the null rule, however, you don't do this because it
                        # affects the current table row, so you might need it to be
                        # called again later. Instead, I just insert a copy whose
                        # state has been advanced one position (since that's all the
                        # null rule means anyway)
                        if len(rule.symbols) > 0:
                            added_rules.append(rule)
                            table[location].append(State(rule, 0, location))
                        else:
                            # Empty rule, this is special
                            copy = self.consumeNonTerminal(rule)
                            copy.data[-1] = rule.finish([], self.reference, Parser.FAIL)
                            table[location].append(copy)


class Parser:
    FAIL = {}  # type: Any

    def __init__(self, rules: List[Rule], start: str) -> None:
        self.rules = rules
        self.start = start
        self.table = []  # type: List[List[State]]
        self.results = []  # type: List[Any]
        self.current = 0
        self.reset()

    def __repr__(self) -> str:
        rules = map(repr, self.rules)
        table = ["{}: {}".format(n, "\n   ".join(map(repr, level))) for n, level in enumerate(self.table)]
        return "Rules:\n{}\nTable:\n{}\n".format("\n".join(rules), "\n".join(table))

    def reset(self) -> None:
        # Clear previous work
        self.results = []
        self.current = 0

        # Setup a table
        added_rules = []
        self.table = [[]]

        # Prepare the table with all rules that match the start name
        for rule in self.rules:
            if rule.name == self.start:
                added_rules.append(rule)
                self.table[0].append(State(rule, 0, 0))
        self.advanceTo(0, added_rules)

    def advanceTo(self, position: int, added_rules: List[Rule]) -> None:
        w = 0
        while w < len(self.table[position]):
            self.table[position][w].process(position, self.table, self.rules, added_rules)
            w += 1

    def feed(self, chunk) -> None:
        for token_pos, token in enumerate(chunk):
            # We add anew states to table[current + 1]
            self.table.append([])

            # Advance all tokens that expect the symbol
            # So for each state in the previous row,

            w = 0
            while w < len(self.table[self.current + token_pos]):
                current_state = self.table[self.current + token_pos][w]
                next_state = current_state.consumeTerminal(token, token_pos)
                if next_state is not None:
                    self.table[self.current + token_pos + 1].append(next_state)
                w += 1

            # Next, for each of the rules, we either
            # (a) complete it, and try to see if the reference row expected that rule
            # (b) predict the next nonterminal it expects by adding that nonterminal's stat state
            # To prevent duplication, we also keep track of rules we have already added.

            added_rules = []  # type: List[Rule]
            self.advanceTo(self.current + token_pos + 1, added_rules)

            # If needed, throw an error
            if len(self.table[-1]) == 0:
                # No states at all! This is not good
                raise ParseError(self.current + token_pos, token, sentence=chunk)

        self.current += len(chunk)

        # Incrementally keep track of results
        self.results = self.finish()

    def finish(self) -> List[List[Any]]:
        # Return the possible parsings
        return [state.data for state in self.table[-1] if
                state.rule.name == self.start
                and state.expect == len(state.rule.symbols)
                and state.reference == 0
                and state.data is not self.FAIL]

    def parse(self, chunk: List[str]) -> List[State]:
        self.reset()
        self.feed(chunk)
        return self.results


def tokenize(sentence: str) -> List[str]:
    return re.compile('\w+|\$[\d\.]+|\S+').findall(sentence)


def parse_rule(line:str, callback: Optional[Callable[[Any, int], Any]] = None) -> Rule:
    match = re.match(r'^(?P<name>\w+) ::= (?P<antecedent>.*)$', line)
    if match is None:
        raise RuleParseException("Cannot parse {}".format(line))
    
    antecedent = [] # type: List[Symbol]
    tokens = match.group("antecedent").split(" ")
    for token in tokens:
        if token.isupper():
            antecedent.append(RuleRef(token))
        elif token != "":
            antecedent.append(Literal(token))

    return Rule(match.group("name"), antecedent, callback)


def parse_syntax(syntax:str) -> List[Rule]:
    rules = []
    for i, line in enumerate(syntax.splitlines()):
        if line == "":
            continue
        
        try:
            rules.append(parse_rule(line))
        except RuleParseException as e:
            raise RuleParseException("{} (line {})".format(str(e), i))
        
    return rules


if __name__ == '__main__':
    # Test simple literals
    # p = Parser([Rule('START', [Literal('a'), Literal('b'), Literal('c')])], 'START')
    # assert len(p.parse(['a', 'b', 'c'])) == 1

    print("Test left recursion")
    p = Parser([
        Rule('A', [RuleRef('A'), Literal('A')]),
        Rule('A', [Literal('A')]),
    ], 'A')
    print(p.parse(list('AAAA')))

    print("Test right recursion")
    p = Parser([
        Rule('A', [Literal('A'), RuleRef('A')]),
        Rule('A', [Literal('A')]),
    ], 'A')
    print(p.parse(list('AAAA')))

    class Digit(Symbol):
        def test(self, literal: str, position: int) -> bool:
            return literal.isdigit()


    class Alpha(Symbol):
        def test(self, literal:str, position: int) -> bool:
            return literal.isalpha()

    print("Test custom literal")
    p = Parser([
        Rule('A', [RuleRef('A'), Digit()]),
        Rule('A', [Literal('A')]),
    ], 'A')
    print(p.parse(list('A1234')))


    # Test recursion and the empty rule
    # p = Parser([
    #     Rule('START', [RuleRef('AB')]),
    #     Rule('AB', [Literal('A'), RuleRef('AB'), Literal('B')]),
    #     Rule('AB', [])
    # ], 'START')
    # print(p.parse(list('AAABBB')))

    print("Done.")
