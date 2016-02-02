from parser import parse_syntax, Parser
import re

rules = """
START ::= S .
S ::= IS
S ::= CAN
S ::= CANNOT
S ::= S but S
S ::= S because S
S ::= S and S
IS ::= INSTANCE is TYPE
IS ::= TYPES are TYPES
TYPE ::= a NOUN
TYPES ::= NOUNS
CAN ::= INSTANCE can VERB
CAN ::= TYPES can VERB
CANNOT ::= INSTANCE can not VERB
CANNOT ::= TYPES can not VERB
INSTANCE ::= Henry
NOUN ::= bird
NOUNS ::= birds
NOUN ::= pinguin
NOUNS ::= pingiuns
VERB ::= fly
"""

if __name__ == '__main__':
    try:
        rules = parse_syntax(rules)
        parser = Parser(rules, "START")
        output = parser.tokenize_and_parse("Henry is a bird but Henry can not fly because Henry is a pinguin and pingiuns can not fly .")
        for i, parsing in enumerate(output):
            print("{}: {}".format(i + 1, repr(parsing)))
    except Exception as e:
        print(repr(e))