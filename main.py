import parser
from grammar import rules

sentences = [
    'Jan is punishable because Jan is a thief .',
    'Jan is punishable because Jan is a thief and thieves are punishable .',
    #'When you steal something you are a thief .',
    #'Only when you steal something you are a thief .'
    #'Jan did not steal anything .'
]

for sentence in sentences:
    p = parser.Parser(rules, 'ARGSET')
    p.feed(sentence.split(' '))

    print("\nPossible parses:")
    for n, parse in enumerate(p.results):
        print("{}) {}".format(n, parse))
