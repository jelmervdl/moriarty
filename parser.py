#!/usr/bin/env python3

# Based on https://github.com/Hardmath123/nearley/blob/master/lib/nearley.js

from typing import List, Optional

class ParseError(RuntimeError):
    pass

class Symbol:
    pass


class Terminal(Symbol):
    def test(self, literal):
        raise NotImplementedError("Terminal.test is abstract")


class NonTerminal(Symbol):
    pass


class Literal(Terminal):
    def __init__(self, literal: str):
        self.literal = literal

    def test(self, literal: str):
        return self.literal == literal

    def __repr__(self) -> str:
        return "\"{}\"".format(self.literal)


class Rule(NonTerminal):
    def __init__(self, name: str, symbols: List[Symbol]):
        self.name = name
        self.symbols = symbols

    def __repr__(self, with_cursor_at: int = None) -> str:
        return "{} --> {}".format(self.name, " | ".join(map(repr, self.symbols)))

    def finish(self, data, reference, FAIL):
        print("!!! Finishing {} with data {} and reference {}!".format(self.name, data, reference))
        return [self.name, data]


class RuleRef(NonTerminal):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self, with_cursor_at: int = None) -> str:
        return "{}".format(self.name)


class State:
    def __init__(self, rule: Rule, expect: int, reference: int):
        self.rule = rule
        self.expect = expect
        self.reference = reference
        self.data = []

    def __repr__(self) -> str:
        return "{{}}, from: {}".format(self.rule.__repr__(self.expect), self.reference)

    def nextState(self, data) -> 'State':
        state = State(self.rule, self.expect + 1, self.reference)
        state.data = self.data[:]
        state.data.append(data)
        return state

    def consumeTerminal(self, inp: str) -> Optional['State']:
        print("consumeTerminal {} using {} expecting {}".format(inp, self.rule, self.rule.symbols[self.expect] if len(self.rule.symbols) > self.expect else '>END<'))
        if len(self.rule.symbols) > self.expect \
            and hasattr(self.rule.symbols[self.expect], 'test') \
            and self.rule.symbols[self.expect].test(inp):
            print("Terminal consumed")
            return self.nextState(inp)
        else:
            return None

    def consumeNonTerminal(self, inp: Rule) -> Optional['State']:
        print("consumeNonTerminal {} while expecting {}".format(inp, self.rule.symbols[self.expect]))
        if isinstance(self.rule.symbols[self.expect], NonTerminal) and self.rule.symbols[self.expect].name == inp.name:
            print("Nonterminal consumed")
            return self.nextState(inp)
        else:
            return None

    def process(self, location, table: List[List['State']], rules: List[Rule], added_rules: List[Rule]) -> None:
        if self.expect == len(self.rule.symbols):
            # We have a completed rule
            self.data = self.rule.finish(self.data, self.reference, Parser.FAIL)

            if self.data is not Parser.FAIL:
                w = 0
                # We need a while here because the empty rule will modify table[reference] when location == reference
                while w < len(table[self.reference]):
                    if not isinstance(self.rule, NonTerminal):
                        continue
                    s = table[self.reference][w]
                    x = s.consumeNonTerminal(self.rule)
                    if x is not None:
                        x.data[-1] = self.data
                        table[location].append(x)
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

            if hasattr(expected_symbol, 'name'):
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
                            copy.data[-1] = []
                            table[location].append(copy)

class Parser:
    FAIL = {}

    def __init__(self, rules: List[Rule], start: str):
        self.table = []
        self.rules = rules
        self.start = start

        # Setup a table
        added_rules = []
        self.table.append([])

        # I could be expecting anything
        for rule in self.rules:
            if rule.name == start:
                added_rules.append(rule)
                self.table[0].append(State(rule, 0, 0))
        self.advanceTo(0, added_rules)
        self.current = 0

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
                next_state = current_state.consumeTerminal(token)
                if next_state is not None:
                    self.table[self.current + token_pos + 1].append(next_state)
                w += 1

            # Next, for each of the rules, we either
            # (a) complete it, and try to see if the reference row expected that rule
            # (b) predict the next nonterminal it expects by adding that nonterminal's stat state
            # To prevent duplication, we also keep track of rules we have already added.

            added_rules = []
            self.advanceTo(self.current + token_pos + 1, added_rules)

            # If needed, throw an error
            if len(self.table[-1]) == 0:
                # No states at all! This is not good
                raise ParseError("No possible parsings at {}: '{}'.".format(self.current + token_pos, token))

        self.current += len(chunk)

        # Incrementally keep track of results
        self.results = self.finish()

    def finish(self) -> List[State]:
        # Return the possible parsings
        return [state.data for state in self.table[-1] if \
            state.rule.name == self.start \
            and state.expect == len(state.rule.symbols) \
            and state.reference == 0 \
            and state.data is not self.FAIL]


sentence = ['Jan','is','punishable','because','Jan','is','a','thief','.']
# ACTOR is LABEL because ACTOR is LABEL2

# argument(because(X,Y)) --> statement(X), [because], statement(Y), ['.'].
# statement(isa(A,P)) --> actor(A), [is], predicate(P).
# actor('jan') --> ['Jan'].
# predicate('punishable') --> [punishable].
# predicate(A) --> [a], archetype(A).
# archetype(thief) --> [thief].

def L(value):
    return Literal(value)

def R(name):
    return RuleRef(name)

rules = [
    Rule('ARGUMENT', [R('STATEMENT'), L('because'), R('STATEMENT'), L('.')]),
    Rule('STATEMENT', [R('ACTOR'), L('is'), R('PREDICATE')]),
    Rule('ACTOR', [L('Jan')]),
    Rule('PREDICATE', [L('punishable')]),
    Rule('PREDICATE', [L('a'),R('ARCHETYPE')]),
    Rule('ARCHETYPE', [L('thief')])
]

parser = Parser(rules, 'ARGUMENT')
parser.feed(sentence)

print("\nPossible parses:")
for n, parse in enumerate(parser.results):
    print("{}) {}".format(n, parse))