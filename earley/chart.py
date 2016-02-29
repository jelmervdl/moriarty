#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-

from typing import Optional, Sized
from grammar import Rule

class Chart(Sized):
    def __init__(self, rows) -> None:
        '''An Earley chart is a list of rows for every input word'''
        self.rows = rows

    def __len__(self) -> int:
        '''Chart length'''
        return len(self.rows)

    def __repr__(self) -> str:
        '''Nice string representation'''
        st = '<Chart ({})>\n\t'.format(len(self))
        st+= '\n\t'.join(str(r) for r in self.rows)
        st+= '\n</Chart>'
        return st

    def __contains__(self, row: 'ChartRow') -> bool:
        return row in self.rows

    def add_row(self, row: 'ChartRow') -> None:
        '''Add a row to chart.'''
        assert row not in self.rows, "Row {} already on the chart!".format(row)
        
        self.rows.append(row)


class ChartRow(Sized):
    def __init__(self, rule: Rule, dot: int = 0, start: int = 0, previous: 'ChartRow' = None, completing: 'ChartRow' = None) -> None:
        '''Initialize a chart row, consisting of a rule, a position
           index inside the rule, index of starting chart and
           pointers to parent rows'''
        self.rule = rule
        self.dot = dot
        self.start = start
        self.completing = completing
        self.previous = previous

    def __len__(self) -> int:
        '''A chart's length is its rule's length'''
        return len(self.rule)

    def __repr__(self) -> str:
        '''Nice string representation:
            <Row <LHS -> RHS .> [start]>'''
        rhs = list(self.rule.rhs)
        rhs.insert(self.dot, '·')
        rule_str = "[{0} -> {1}]".format(self.rule.lhs, ' '.join(rhs))
        return "<Row {0} [{1}]>".format(rule_str, self.start)

    def __eq__(self, other) -> bool:
        '''Two rows are equal if they share the same rule, start and dot'''
        return self.dot == other.dot \
           and self.start == other.start \
           and self.rule == other.rule

    def is_complete(self) -> bool:
        '''Returns true if rule was completely parsed, i.e. the dot is at the end'''
        return len(self) == self.dot

    def next_category(self) -> Optional[str]:
        '''Return next category to parse, i.e. the one after the dot'''
        if self.dot < len(self):
            return self.rule[self.dot]
        return None

    def prev_category(self) -> Optional[str]:
        '''Returns last parsed category'''
        if self.dot > 0:
            return self.rule[self.dot-1]
        return None

