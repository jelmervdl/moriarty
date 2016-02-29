#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

from typing import Sized, List
import sys

class Rule(Sized):
    def __init__(self, lhs: str, rhs: List[str]) -> None:
        '''Initializes grammar rule: LHS -> [RHS]'''
        self.lhs = lhs
        self.rhs = rhs

    def __len__(self) -> int:
        '''A rule's length is its RHS's length'''
        return len(self.rhs)

    def __repr__(self) -> str:
        '''Nice string representation'''
        return "<Rule {0} -> {1}>".format(self.lhs, ' '.join(self.rhs))

    def __getitem__(self, item: int) -> str:
        '''Return a member of the RHS'''
        return self.rhs[item]

    def __eq__(self, other) -> bool:
        '''Rules are equal iff both their sides are equal'''
        return self.lhs == other.lhs and self.rhs == other.rhs


class Terminal:
    def __init__(self, lhs:str) -> None:
        self.lhs = lhs

    def accepts(self, word:str) -> bool:
        return False


class Literal(Terminal):
    def __init__(self, lhs: str, word: str) -> None:
        super().__init__(lhs)
        self.word = word

    def accepts(self, word: str):
        return self.word == word


class Grammar:
    def __init__(self):
        '''A grammar is a collection of rules, sorted by LHS'''
        self.rules = {}
        self.terminals = []

    def __repr__(self):
        '''Nice string representation'''
        st = '<Grammar>\n'
        for group in self.rules.values():
            for rule in group:
                st+= '\t{0}\n'.format(str(rule))
        st+= '</Grammar>'
        return st

    def __getitem__(self, lhs: str) -> List[Rule]:
        '''Return rules for a given LHS'''
        if lhs in self.rules:
            return self.rules[lhs]
        else:
            return []

    def tags_for_word(self, word: str) -> List[str]:
        return [terminal.lhs for terminal in self.terminals if terminal.accepts(word)]
    
    def add_rule(self, rule: Rule) -> None:
        '''Add a rule to the grammar'''
        lhs = rule.lhs
        if lhs in self.rules:
            self.rules[lhs].append(rule)
        else:
            self.rules[lhs] = [rule]

    def add_terminal(self, terminal: Terminal) -> None:
        self.terminals.append(terminal)

    @staticmethod
    def from_file(filename):
        '''Returns a Grammar instance created from a text file.
           The file lines should have the format:
               lhs -> outcome | outcome | outcome'''

        grammar = Grammar()
        for line in open(filename):
            # ignore comments
            line = line[0:line.find('#')]
            if len(line) < 3:
                continue

            rule = line.split('->')
            lhs = rule[0].strip()
            for outcome in rule[1].split('|'):
                rhs = outcome.strip()
                symbols = rhs.split(' ') if rhs else []
                r = Rule(lhs, symbols)
                grammar.add_rule(r)

        return grammar

