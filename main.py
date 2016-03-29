import parser
from grammar import parse_grammar

p = None

with open('grammar.txt', 'r') as fh:
    rules, sentences = parse_grammar(fh)
    p = parser.Parser(rules, 'START')

    for rule in rules:
        print(rule)

    for sentence in sentences:
        print(sentence)
        try:
            tokens = parser.tokenize(sentence)
            output = p.parse(tokens)
            print(output)
        except parser.ParseError as e:
            print(e)
            # print(p.table)
