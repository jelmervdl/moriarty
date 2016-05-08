import sys
import parser
from grammar import parse_grammar

def test_grammar(grammar_path):
    with open(grammar_path, 'r') as fh:
        rules, sentences = parse_grammar(fh)
        p = parser.Parser(rules, 'START')

        for rule in rules:
            print(rule)

        for sentence in sentences:
            print(sentence)
            try:
                tokens = parser.tokenize(sentence)
                output = p.parse(tokens)
                
                if len(output) == 0:
                    print("No possible parses")
                else:
                    for n, parse in enumerate(output):
                        print("{}: {}\n".format(n, parse))

            except parser.ParseError as e:
                print(e)
                # print(p.table)

        return p

for grammar_path in sys.argv[1:]:
    test_grammar(grammar_path)