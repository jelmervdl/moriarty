#!/usr/bin/python
# coding=utf-8
# -*- encoding: utf-8 -*-
from typing import List

from chart import Chart, ChartRow
from grammar import Grammar, Rule

class ParseError(Exception):
    pass

class Parser:
    GAMMA_SYMBOL = 'GAMMA'

    def __init__(self, grammar: Grammar, debug: bool = False) -> None:
        '''Initialize parser with grammar and sentence'''
        self.grammar = grammar
        self.debug = debug

    def log(self, text):
        if self.debug:
            print(text)

    def init_first_chart(self) -> None:
        '''Add initial Gamma rule to first chart'''
        row = ChartRow(Rule(Parser.GAMMA_SYMBOL, ['S']), 0, 0)
        self.charts[0].add_row(row)

    def prescan(self, sentence: List[str], chart: Chart, position: int) -> None:
        '''Scan current word in sentence, and add appropriate
           grammar categories to current chart'''
        word = sentence[position-1]
        tags = self.grammar.tags_for_word(word)
        if tags:
            for tag in tags:
                self.log("Prescan add tag '{}' for word '{}' at pos {}".format(tag, word, position - 1))
                chart.add_row(ChartRow(Rule(tag, [word]), 1, position-1))
        else:
            raise ParseError("Cannot tag word '{}' at position {} ({})".format(word, position, chart))

    def predict(self, chart: Chart, position: int) -> None:
        '''Predict next parse by looking up grammar rules
           for pending categories in current chart'''
        for row in chart.rows:
            next_cat = row.next_category()
            if next_cat:
                self.log("Predicting rules for cat '{}'".format(next_cat))
                rules = self.grammar[next_cat]
                for rule in rules:
                    new = ChartRow(rule, 0, position)
                    if new not in chart:
                        self.log("Predict: Adding row '{}' to chart".format(new))
                        chart.add_row(new)

    def complete(self, chart: Chart, position: int) -> None:
        '''Complete a rule that was done parsing, and
           promote previously pending rules'''
        for row in chart.rows:
            if row.is_complete():
                for r in self.charts[row.start].rows:
                    if not r.is_complete() and row.rule.lhs == r.next_category():
                        new = ChartRow(rule=r.rule, dot=r.dot+1, start=r.start, previous=r, completing=row)
                        # if new.is_complete():
                        #     prev = new.previous
                        #     steps = [prev]
                        #     while prev and prev.rule.lhs == new.rule.lhs:
                        #         steps.append(prev)
                        #         prev = prev.previous
                        #         self.log("\nAbout to add complete row for rule '{}' with prev {} and completing {} and complete row {}: \n\t{}\n".format(new.rule, new.previous, new.completing, row, "\n\t".join(map(repr, reversed(steps)))))
                        if new not in chart:
                            self.log("Complete: Adding row '{}' to chart".format(new))
                            chart.add_row(new)

    def parse(self, sentence: List[str]):
        '''Main Earley's Parser loop'''
        
        # prepare a chart for every input word
        self.charts = [Chart([]) for i in range(len(sentence) + 1)]
        
        # add initial Gamma rule to first chart
        self.init_first_chart()

        i = 0
        # we go word by word
        while i < len(self.charts):
            chart = self.charts[i]
            self.prescan(sentence, chart, i) # scan current input

            # predict & complete loop
            # rinse & repeat until chart stops changing
            length = len(chart)
            old_length = -1
            while old_length != length:
                self.predict(chart, i)
                self.complete(chart, i)

                old_length = length
                length = len(chart)

            i+= 1

        # finally, print charts for debuggers
        if self.debug:
            print("Parsing charts:")
            for i in range(len(self.charts)):
                print("-----------{0}-------------".format(i))
                print(self.charts[i])
                print("-------------------------".format(i))

        return [row for row in self.charts[-1].rows if row.start == 0 and row.is_complete() and row.rule.lhs == self.GAMMA_SYMBOL]
        

    def parsed(self):
        '''Returns true if sentence has a complete parse tree'''
        res = False
        for row in self.charts[-1].rows:
            if row.start == 0 and row.rule.lhs == self.GAMMA_SYMBOL:
                    if row.is_complete():
                        self.complete_parses.append(row)
                        res = True
        return res

