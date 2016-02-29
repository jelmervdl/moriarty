from grammar import Rule, Terminal, Grammar
from parser import Parser
from parse_trees import ParseTrees

class Verb(Terminal):
    def accepts(self, word: str) -> bool:
        return word in ['krijgt', 'koopt', 'is']

class Det(Terminal):
    def accepts(self, word: str) -> bool:
        return word in ['de', 'het', 'een']

class Noun(Terminal):
    def accepts(self, word: str) -> bool:
        '''Almost anything can be a noun'''
        return word.isalpha()

class Name(Terminal):
    def accepts(self, word: str) -> bool:
        '''Names always begin with a capital'''
        return word[0].isupper()


grammar = Grammar()
grammar.add_rule(Rule('S', ['NAME','VERB','TYPE']))
grammar.add_rule(Rule('TYPE', ['DET','NOUN']))

grammar.add_terminal(Name('NAME'))
grammar.add_terminal(Verb('VERB'))
grammar.add_terminal(Det('DET'))
grammar.add_terminal(Noun('NOUN'))

parser = Parser(grammar,debug=True)

parses = parser.parse(["Jan","is","een", "dief"])
print(parses)

print(ParseTrees(parser, parses))