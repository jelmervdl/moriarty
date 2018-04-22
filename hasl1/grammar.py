#!/usr/bin/env python

import sys
import traceback
import operator
import re
from pprint import pprint
from functools import reduce
from itertools import chain
from typing import NamedTuple, Tuple

import spacy

import english
import parser
from parser import Rule, RuleRef, passthru


def coalesce(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None


def merge(state, data):
    return reduce(operator.__add__, data)


def indent(text, prefix='\t'):
    return '\n'.join(prefix + line for line in text.split('\n'))


def unique(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]


def singular_verb(verb):
    mapping = {
        'are': 'is',
        'can': 'can',
    }
    singular = mapping[verb.text] if verb.text in mapping else verb.tokens[0].lemma_ + 's'
    return Span(verb.start, verb.end, [singular])


class Stamper(object):
    def __init__(self):
        self.seq = 0
        self.attr = '_id_stamp'

    def next(self):
        self.seq += 1
        return self.seq

    def read(self, obj):
        if not hasattr(obj, self.attr):
            raise Exception("Object {!r} has no id yet".format(obj))
        return getattr(obj, self.attr)

    def __call__(self, obj):
        if not hasattr(obj, self.attr):
            setattr(obj, self.attr, self.next())
        return getattr(obj, self.attr)


id = Stamper()


def print_pos_tags(doc):
    el_cnt = 3
    tokens = []
    for token in doc:
        tokens.append([
            str(token),
            str(token.pos_),
            str(token.tag_)
        ])
    
    lines = [[[] for _ in range(el_cnt)]]
    line_length = 0
    for token in tokens:
        token_length = max(len(el) for el in token)
        if line_length + token_length + 1 > 80:
            lines.append([[] for _ in range(el_cnt)])
            line_length = 0
        for n in range(el_cnt):
            lines[-1][n].append(token[n].ljust(token_length))
        line_length += token_length + 1

    for line in lines:
        for el_line in line:
            print(' '.join(el_line))
        print()


sentences = [
    'Socrates is mortal but Socrates is not mortal.',
    'Socrates is mortal but he is not mortal.',
    'Socrates is mortal because he is a man and men are mortal.',
    'Socrates is mortal because men are mortal and he is a man.',
    'Tweety can fly because Tweety is a bird and birds can fly. Tweety can fly but Tweety is a penguin.',
    'Tweety can fly because Tweety is a bird and birds can fly. Tweety is a bird but Tweety is a penguin.',
    'Tweety can fly because Tweety is a bird and birds can fly. birds can fly but Tweety is a penguin.',
    
    'Tweety can fly because Tweety is a bird and birds can fly but Tweety can not fly because Tweety is a penguin.',
    'Tweety can fly because Tweety is a bird and birds can fly but Tweety is a penguin and penguins can not fly.',
    
    'The object is red because the object appears red but it is illuminated by a red light.',
    'Harry is a British subject because Harry was born in Bermuda and a man born in Bermuda is a British subject because of the following statutes and legal provisions but Harry has become a naturalized American.',
];

# sentences = [
#     'Socrates is mortal because he is a man and he is not a god.',
#     'Socrates is mortal because he is a man and he is not a god because gods are not mortal.',
#     'Socrates is mortal because men are mortal.',
# ]

reed_sentences = [
    'Bob Sturges can not have a telephone because his name is not listed in the phone book.'
]

hasl0_sentences = [
    'Socrates is mortal because he is a man and men are mortal.',
    'The object is red because the object appears red but it is illuminated by a red light.',
    'Tweety can fly because he is a bird. He is a bird because he has wings.'
]

claims = [
    'Socrates is mortal',
    'he is a man',
    'men are mortal',
    'Tweety can fly',
    'Tweety is a bird',
    'birds can fly',
    'Tweety is a penguin',
    'penguins can not fly',
    'The object is red',
    'the object appears red',
    'it is illuminated by a red light',
    'Harry is a British subject',
    'Harry was born in Bermuda',
    'a man born in Bermuda is a British subject',
    'the following statutes and legal provisions',
    'Harry has become a naturalized American',
]


class Mapping(object):
    def __init__(self, entries = []):
        self.entries = dict(entries)
        for key in self.entries.keys():
            while id.read(self.entries[key]) != id.read(self.entries[id(self.entries[key])]):
                self.entries[key] = self.entries[id.read(self.entries[key])]

    def __add__(self, other):
        return Mapping(chain(self.entries.items(), other.entries.items()))

    def __getitem__(self, obj):
        if isinstance(obj, list):
            return list(self[el] for el in obj)
        else:
            return self.entries[id.read(obj)] if id(obj) in self.entries else obj

    def __setitem__(self, obj, replacement):
        self.entries[id(obj)] = replacement
        self.entries[id(replacement)] = replacement


class Span(object):
    def __init__(self, start = None, end = None, tokens = []):
        self.start = start
        self.end = end
        self.tokens = tokens

    def __add__(self, other):
        return Span(coalesce(self.start, other.start), coalesce(other.end, self.end), self.tokens + other.tokens)

    def __str__(self):
        return self.text

    def __repr__(self):
        return '"{}"[{},{}]'.format(self.text, self.start, self.end)

    def __eq__(self, other):
        return other is not None and self.text == other.text

    @property
    def pos(self):
        return slice(self.start, self.end)

    @property
    def text(self):
        return " ".join(str(token) for token in self.tokens)

    def map(self, callback):
        return self.__class__(self.start, self.end, callback(self.text).split(' '))


class Tag(parser.Symbol):
    def __init__(self, tag):
        self.tag = re.compile(tag)

    def __repr__(self):
        return '<{}>'.format(self.tag.pattern)

    def test(self, literal, position, state):
        return self.tag.fullmatch(literal.tag_)

    def finish(self, literal, position, state):
        return Span(position, position + 1, [literal])


class Literal(parser.Symbol):
    def __init__(self, literal):
        self.literal = literal

    def __repr__(self):
        return '"{}"'.format(self.literal)

    def test(self, literal, position, state):
        return str(literal) == self.literal

    def finish(self, literal, position, state):
        return Span(position, position + 1, [literal])


if __name__ == '__main__':
    nlp = spacy.load('en', disable=['parser', 'ner', 'textcat'])

    def test(p, sentences):
        selection = frozenset(map(int, sys.argv[1:]))
        for n, sentence in enumerate(sentences, 1):
            if len(selection) > 0 and n not in selection:
                continue
            doc = nlp(sentence)
            print("{})".format(n))
            print_pos_tags(doc)
            try:
                parses = p.parse(doc)
                print("There are {} parses".format(len(parses)))
                datas = set(parse['data'] for parse in parses)
                pprint(datas)
                # for parse in parses:
                #     print("Parse:")
                #     pprint(parse['data'])
                #     print("Tree:")
                #     pprint(parse['tree'])

            except parser.ParseError as e:
                print("Failure: {}".format(e))
            print()
else:
    def test(p, sentences):
        """test as a no-op when pos_tags is loaded as library"""
        pass

class Entity(object):
    def __init__(self, name = None, noun = None, pronoun = None):
        self.name = name
        self.noun = noun
        self.pronoun = pronoun

    def __str__(self):
        return str(self.span) if self.span else 'something'

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return self.name == other.name \
            and self.noun == other.noun \
            and self.pronoun == other.pronoun

    def __repr__(self):
        return "({} name={name} noun={noun} pronoun={pronoun})".format(id(self), **self.__dict__)

    @property
    def span(self):
        if self.name is not None:
            return self.name
        if self.noun is not None:
            return self.noun
        if self.pronoun is not None:
            return self.pronoun
        else:
            return None

    @property
    def pos(self):
        parts = [self.name, self.noun, self.pronoun]
        positions = [part.pos for part in parts if part is not None]
        return min(positions) if len(positions) > 0 else None

    def merge(self, other):
        """Merge this instance with one that refers to me"""
        return Entity(
            name = self.name,
            noun = self.noun if self.noun is not None else other.noun,
            pronoun = self.pronoun if self.pronoun is not None else other.pronoun)

    def refers_to(self, other):
        """Test whether this instance refers to a (better defined) other instance"""
        if self.name:
            return self.name == other.name
        elif self.noun:
            return self.noun == other.noun
        elif self.pronoun:
            if other.pronoun:
                return self.pronoun == other.pronoun
            else:
                return other.name is not None or other.noun is not None
        else:
            return False



class Claim(object):
    def __init__(self, subj, verb, obj, *, negated=False, assumed=False):
        self.subj = subj
        self.verb = verb
        self.obj = obj
        self.negated = negated
        self.assumed = assumed

    def __eq__(self, other):
        return str(self).lower() == str(other).lower()

    def __str__(self):
        return "{subj} {verb} {neg}{obj}".format(neg="not " if self.negated else "", **self.__dict__)

    def __repr__(self):
        return "{ass}{neg}{subj!r} {verb!r} {obj!r}".format(ass="assume " if self.assumed else "", neg = "not " if self.negated else "", **self.__dict__)

    def __hash__(self):
        return hash(str(self))

    @property
    def entities(self):
        if isinstance(self.subj, Entity):
            yield self.subj

    def counters(self, other):
        return self.subj == other.subj \
            and self.verb == other.verb \
            and self.obj == other.obj \
            and self.negated != other.negated

    def update(self, mapping):
        return Claim(mapping[self.subj], mapping[self.verb], mapping[self.obj], negated=self.negated, assumed=self.assumed)


class Relation(object):
    arrows = {
        'attack': '~*',
        'support': '~>'
    }

    def __init__(self, type, sources, target):
        assert type in self.arrows
        self.type = type
        
        assert all(isinstance(source, Claim) for source in sources)
        self.sources = tuple(sources)

        assert isinstance(target, Claim) or isinstance(target, Relation)
        self.target = target

    def __str__(self):
        return "({} {} {})".format(' ^ '.join(str(s) for s in self.sources), self.arrows[self.type], self.target)

    def __repr__(self):
        return "{} ({!r}) {} ({!r})".format(self.type, self.sources, self.arrows[self.type], self.target)

    def __hash__(self):
        return hash((self.type, self.sources, self.target))

    def __eq__(self, other):
        return isinstance(other, Relation) \
            and self.type == other.type \
            and frozenset(self.sources) == frozenset(other.sources) \
            and self.target == other.target

    def update(self, mapping):
        return Relation(self.type,
            sources = tuple(mapping[source] for source in self.sources),
            target = mapping[self.target])


class Consolidation(NamedTuple):
    claims: Tuple[Claim, ...]
    relations: Tuple[Relation, ...]
    mapping: Mapping


class Argument(object):
    def __init__(self, claims = tuple(), relations = tuple()):
        assert all(isinstance(claim, Claim) for claim in claims)
        assert all(isinstance(relation, Relation) for relation in relations)
        consolidation = self.__class__.consolidate(claims, relations)
        self.claims = consolidation.claims
        self.relations = consolidation.relations

    @property
    def roots(self):
        return [claim for claim in self.claims if all(claim not in relation.sources for relation in self.relations)]

    @property
    def root(self):
        return self.roots[0]

    def __repr__(self):
        return "Claims:\n{}\nRelations:\n{}".format(
            indent("\n".join(str(p) for p in self.claims), "  "),
            indent("\n".join(str(r) for r in self.relations), "  "))

    def __add__(self, other):
        return self.__class__(claims = self.claims + other.claims, relations = self.relations + other.relations)

    def __hash__(self):
        return hash((self.claims, self.relations))

    def __eq__(self, other):
        return isinstance(other, Argument) \
            and frozenset(self.claims) == frozenset(other.claims) \
            and frozenset(self.relations) == frozenset(other.relations)

    @staticmethod
    def consolidate(claims, relations):
        def replace(old, new, list):
            old_ids = frozenset(id(el) for el in old)
            for el in list:
                if id(el[1]) in old_ids:
                    el[1] = new

        entities = [[id(entity), entity] for entity in sorted((entity for entity in chain.from_iterable(claim.entities for claim in claims) if entity.pos is not None), key=lambda entity: entity.pos)]

        c = len(entities)
        for m, entity in enumerate(entities[:c]):
            for n, other_entity in enumerate(entities[m+1:c], m+1):
                result = other_entity[1].refers_to(entity[1])
                # print("Does {!r} ({}) refer to {!r} ({}): {!r}".format(other_entity[1], id(other_entity[1]), entity[1], id(entity[1]), result))
                if result:
                    merged = entity[1].merge(other_entity[1])
                    entities.append([id(merged), merged])
                    replace((entity[1], other_entity[1]), merged, entities)

        mapping = Mapping(entities)

        entries = [[id(claim), claim] for claim in claims]

        # Update all claims with the new entities
        for entry in entries[0:len(entries)]: # to prevent iterating over new items
            updated = entry[1].update(mapping)
            entry[1] = updated
            entries.append([id(updated), updated])

        # Merge all claims that are (or have become) equal
        for m, entry in enumerate(entries):
            for n, other_entry in enumerate(entries[m:], m):
                if entry[1] == other_entry[1]:
                    entries[n][1] = entry[1]

        mapping += Mapping(entries)
        
        new_relations = []
        for i, relation in enumerate(relations):
            updated = relation.update(mapping)
            new_relations.append(updated)
            mapping[relation] = updated

        return Consolidation(
            claims=tuple(entry[1] for entry in entries if entry[0] == id(entry[1])),
            relations=tuple(new_relations),
            mapping=mapping)


class Grammar(object):
    def __init__(self, rules = None):
        self.rules = rules if rules is not None else []

    def __iter__(self):
        return iter(self.rules)

    def __add__(self, other):
        return self.__class__(list(self.rules) + list(other))

    def without(self, names):
        return self.__class__(rule for rule in self.rules if rule.name not in names)

    def rule(self, name, symbols):
        rule = Rule(name, symbols)
        self.rules.append(rule)
        def wrapper(callback):
            rule.callback = lambda state, data: callback(*data)
            return callback
        return wrapper


en_grammar = Grammar([
    Rule('name', [Tag('NNP')], merge),
    Rule('name', [RuleRef('name'), Tag('NNP')], merge), # longer names
    Rule('name', [RuleRef('name'), Tag('NNPS')], merge), # Catholic Swedes
    Rule('name', [Literal('Tweety')], merge),
    
    Rule('instance', [RuleRef('name')],
        lambda state, data: Entity(name=data[0])),
    Rule('instance', [Tag('PRP')],
        lambda state, data: Entity(pronoun=data[0])),
    Rule('instance', [RuleRef('def-dt'), RuleRef('adjectives?'), RuleRef('noun')],
        lambda state, data: Entity(noun=data[0] + data[1] + data[2])),
    Rule('instance', [RuleRef('def-dt'), RuleRef('adjectives?'), RuleRef('noun'), RuleRef('prep-phrase')],
        lambda state, data: Entity(noun=data[0] + data[1] + data[2] + data[3])),
    Rule('instance', [Tag('PRP\\$'), Tag('NNP?')], # his name
        lambda state, data: Entity(noun=data[0] + data[1])),

    Rule('adjectives?', [RuleRef('adjectives')], merge),
    Rule('adjectives?', [], lambda state, data: Span()),

    Rule('adjectives', [Tag('JJ')], merge),
    Rule('adjectives', [Tag('JJ'), RuleRef('adjectives')], merge),

    Rule('noun-sg', [Tag('NN')], merge),
    Rule('noun-sg', [Tag('NN'), RuleRef('noun-sg')], merge),

    Rule('noun-pl', [Tag('NNS')], merge),
    Rule('noun-pl', [Tag('NNS'), RuleRef('noun-pl')], merge),

    Rule('noun', [RuleRef('noun-sg')], merge),
    Rule('noun', [RuleRef('noun-pl')], merge),

    Rule('object', [RuleRef('name')], merge),
    Rule('object', [RuleRef('noun')], merge),
    Rule('object', [RuleRef('instance')], lambda state, data: data[0].span),
    Rule('object', [RuleRef('adjectives')], merge),
    Rule('object', [RuleRef('adjectives'), RuleRef('prep-phrase')], merge),
    Rule('object', [Tag('DT'), RuleRef('adjectives?'), RuleRef('noun')], merge),
    Rule('object', [Tag('DT'), RuleRef('adjectives?'), RuleRef('name')], merge),
    # Rule('object', [RuleRef('vbn')], merge), # (is) born, (can) fly
    Rule('object', [RuleRef('object'), RuleRef('vbn')], merge), # a man born in Bermuda
    Rule('object', [RuleRef('object'), RuleRef('prep-phrase')], merge), # an act of John

    Rule('object', [Tag('VBG'), RuleRef('object')], merge), # encouraging waste

    Rule('object', [Tag('JJR?'), Tag('IN'), Tag('CD'), Tag('NN')], merge), # less than 2%

    Rule('ability', [Tag('VB')], merge),
    Rule('ability', [Tag('VB'), RuleRef('object')], merge),
    Rule('ability', [Tag('VB'), RuleRef('vbn')], merge),

    Rule('prototype-sg', [RuleRef('indef-dt'), RuleRef('noun-sg')], merge),
    Rule('prototype-sg', [RuleRef('indef-dt'), RuleRef('noun-sg'), RuleRef('vbn')], merge),

    Rule('prototype-pl', [RuleRef('noun-pl')], lambda state, data: Span(None, None, ['a']) + data[0].map(english.singularize)),
    Rule('prototype-pl', [RuleRef('noun-pl'), RuleRef('vbn')], lambda state, data: Span(None, None, ['a']) + data[0].map(english.singularize) + data[1]),

    Rule('vbn', [Tag('VBN')], passthru),
    Rule('vbn', [Tag('VBN'), RuleRef('prep-phrase')], merge),

    Rule('prep-phrase', [Tag('IN'), Tag('NNP')], merge), # for "In Bermuda"
    Rule('prep-phrase', [Tag('IN'), RuleRef('object')], merge), # for "by a red light"

    Rule('prep-phrase', [RuleRef('adverbs'), Tag('TO'), Tag('VB'), RuleRef('object')], merge),

    Rule('def-dt', [Literal('The')], passthru),
    Rule('def-dt', [Literal('the')], passthru),
    Rule('def-dt', [Literal('this')], passthru),

    Rule('indef-dt', [Literal('a')], passthru),

    Rule('sentences',   [RuleRef('sentences'), RuleRef('sentence')], lambda state, data: data[0] + data[1]),
    Rule('sentences',   [RuleRef('sentence')], passthru),
    Rule('sentence',    [RuleRef('argument'), Literal('.')], passthru),

    Rule('adverbs', [Tag('RB')], merge),
    Rule('adverbs', [RuleRef('adverbs'), Tag('RB')], merge),
])

hasl0_grammar = en_grammar + [
    Rule('minor-claim', [RuleRef('instance'), Tag('VBZ'), RuleRef('object')],
        lambda state, data: Claim(data[0], data[1], data[2])),
    Rule('minor-claim', [RuleRef('instance'), Tag('MD'), Tag('VB')],
        lambda state, data: Claim(data[0], data[1], data[2])),
    
    Rule('major-claim', [Tag('NNS'), Tag('VB[PD]'), RuleRef('object')],
        lambda state, data: Claim(data[0], data[1], data[2])),
    Rule('major-claim', [Tag('NNS'), Tag('MD'), Tag('VB')],
        lambda state, data: Claim(data[0], data[1], data[2])),
    
    Rule('claim', [RuleRef('major-claim')], passthru),
    Rule('claim', [RuleRef('minor-claim')], passthru),


    Rule('minor-claims', [RuleRef('minor-claim')],
        lambda state, data: (data[0],)),
    Rule('minor-claims', [RuleRef('minor-claim-list'), Literal('and'), RuleRef('minor-claim')],
        lambda state, data: (*data[0], data[2])),
    Rule('minor-claim-list', [RuleRef('minor-claim')],
        lambda state, data: (data[0],)),
    Rule('minor-claim-list', [RuleRef('minor-claim-list'), Literal(','), RuleRef('minor-claim')],
        lambda state, data: (*data[0], data[2])),

    Rule('argument',    [RuleRef('support')], passthru),
    Rule('argument',    [RuleRef('attack')], passthru),
    Rule('argument',    [RuleRef('warranted-support')], passthru),
    Rule('argument',    [RuleRef('undercutter')], passthru),
]

@hasl0_grammar.rule('support', [RuleRef('claim'), Literal('because'), RuleRef('minor-claims')])
def support(conclusion, marker, minors):
    """a <- b+"""
    return Argument(claims=(conclusion,) + minors, relations=(Relation('support', minors, conclusion),))

@hasl0_grammar.rule('attack', [RuleRef('claim'), Literal('but'), RuleRef('minor-claims')])
def support(conclusion, marker, minors):
    """a *- b+"""
    return Argument(claims=(conclusion, *minors), relations=[Relation('attack', minors, conclusion)])

@hasl0_grammar.rule('warranted-support', [RuleRef('claim'), Literal('because'), RuleRef('minor-claim-list'), Literal('and'), RuleRef('major-claim')])
def warranted_support_minor_major(conclusion, marker, minors, conj, major):
    """(a <- b+) <- c"""
    support = Relation('support', minors, conclusion)
    warrant = Relation('support', (major,), support)
    return Argument(claims=(conclusion, *minors, major), relations=(support, warrant))

@hasl0_grammar.rule('warranted-support', [RuleRef('claim'), Literal('because'), RuleRef('major-claim'), Literal('and'), RuleRef('minor-claims')])
def warranted_support_major_minor(conclusion, marker, major, conj, minors):
    """(a <- c+) <- b"""
    support = Relation('support', minors, conclusion)
    warrant = Relation('support', (major,), support)
    return Argument(claims=(conclusion, major, *minors), relations=(support, warrant))

@hasl0_grammar.rule('warranted-attack', [RuleRef('claim'), Literal('because'), RuleRef('minor-claim-list'), Literal('and'), RuleRef('major-claim')])
def warranted_attack_minor_major(conclusion, marker, minors, conj, major):
    """(a <- b+) <- c"""
    attack = Relation('attack', minors, conclusion)
    warrant = Relation('support', (major,), attack)
    return Argument(claims=(conclusion, *minors, major), relations=(attack, warrant))

@hasl0_grammar.rule('warranted-attack', [RuleRef('claim'), Literal('because'), RuleRef('major-claim'), Literal('and'), RuleRef('minor-claims')])
def warranted_attack_major_minor(conclusion, marker, major, conj, minors):
    """(a <- c+) <- b"""
    attack = Relation('attack', minors, conclusion)
    warrant = Relation('support', (major,), attack)
    return Argument(claims=(conclusion, major, *minors), relations=(attack, warrant))


"""
> (a because b) but c: (a<-b)<-c
Tweety is a bird because Tweety can fly but planes can also fly
Tweety is a bird because Tweety can fly but Tweety was thrown
Conclusie: zinloos om iets achter te zetten -> geval apart. Also de enige manier om deze te construeren.
"""
@hasl0_grammar.rule('undercutter', [RuleRef('claim'), Literal('because'), RuleRef('minor-claims'), Literal('but'), RuleRef('claim')])
def undercutter(conclusion, because, minors, but, attack):
    """(a <- b+) *- c (c can be both minor and major)"""
    support = Relation('support', minors, conclusion)
    undercutter = Relation('attack', (attack,), support)
    return Argument(claims=(conclusion, *minors, attack), relations=(support, undercutter))

# test(parser.Parser(hasl0_grammar, 'sentences'), hasl0_sentences)

###
### Recursion
###

hasl1_grammar = hasl0_grammar.without({'major-claim'}) + [
    Rule('argument',    [RuleRef('minor-argument')], passthru),
    Rule('argument',    [RuleRef('major-argument')], passthru),
]

@hasl1_grammar.rule('minor-arguments', [RuleRef('minor-argument')])
def hasl1_argued_minor_claims_single(minor):
    return minor

@hasl1_grammar.rule('minor-arguments', [RuleRef('minor-claim-list'), Literal('and'), RuleRef('minor-argument')])
def hasl1_argued_minor_claims_multiple(list, conj, minor):
    return Argument(claims=[*list, *minor.claims], relations=minor.relations)

@hasl1_grammar.rule('minor-claim-list', [RuleRef('minor-claim')])
def hasl1_minor_claims_list_single(minor):
    return (minor,)

@hasl1_grammar.rule('minor-claim-list', [RuleRef('minor-claim-list'), Literal(','), RuleRef('minor-claim')])
def hasl1_minor_claims_list_multiple(list, conj, minor):
    return (*list, minor)


@hasl1_grammar.rule('minor-claim', [RuleRef('instance'), Tag('VBZ'), RuleRef('adverbs'), RuleRef('object')])
def hasl1_minor_claim_vbz_obj(subj, verb, neg, obj):
    return Claim(subj, verb, obj, negated=True)

@hasl1_grammar.rule('minor-claim', [RuleRef('instance'), Tag('MD'), RuleRef('adverbs'), RuleRef('ability')])
def hasl1_negated_minor_claim_md_vb(subj, verb, neg, obj):
    return Claim(subj, verb, obj, negated=True)

@hasl1_grammar.rule('minor-claim', [RuleRef('instance'), Tag('VB[DZ]'), RuleRef('vbn')])
def hasl1_minor_claim_vbdz_vbn(subj, verb, obj):
    return Claim(subj, verb, obj)

@hasl1_grammar.rule('minor-argument', [RuleRef('minor-claim'), Literal('because'), RuleRef('minor-arguments')])
def hasl1_support_minor(conclusion, because, minors):
    """a <- b+"""
    support = Relation('support', minors.roots, conclusion)
    return Argument(claims=[conclusion, *minors.claims], relations=[support, *minors.relations])

@hasl1_grammar.rule('major-argument', [RuleRef('major-claim'), Literal('because'), RuleRef('minor-arguments')])
def hasl1_support_major(conclusion, because, minors):
    """A <- b+"""
    support = Relation('support', minors.roots, conclusion)
    return Argument(claims=[conclusion, *minors.claims], relations=[support, *minors.relations])

@hasl1_grammar.rule('minor-argument', [RuleRef('minor-claim'), Literal('because'), RuleRef('major-claim'), Literal('and'), RuleRef('minor-arguments')])
def hasl1_warranted_support_major_minor(conclusion, because, major, conj, minors):
    """(a <- c) <- B"""
    support = Relation('support', minors.roots, conclusion)
    warrant = Relation('support', [major], support)
    return Argument(claims=[conclusion, major, *minors.claims], relations=[support, warrant, *minors.relations])

@hasl1_grammar.rule('minor-argument', [RuleRef('minor-claim'), Literal('because'), RuleRef('minor-claim-list'), Literal('and'), RuleRef('major-argument')])
def hasl1_warranted_support_minor_major(conclusion, because, minors, conj, major):
    """(a <- b) <- C"""
    support = Relation('support', minors, conclusion)
    warrant = Relation('support', [major.root], support)
    return Argument(claims=[conclusion, *minors, *major.claims], relations=[*major.relations, support, warrant])

# a because b and because c?
# <specific-argument> ::= <specific-claim> <reasons>

# <reasons> ::= <reason-list> `and' <reason>

# <reason-list> ::= <reason-list> `,' <reason>
# \alt <reason>

# <reason> ::= `because' <specific-argument>

@hasl1_grammar.rule('minor-argument', [RuleRef('minor-claim'), RuleRef('reasons')])
def hasl1_minr_argument_support_reasons(conclusion, reasons):
    reasons_claims = reduce(lambda claims, reason: claims + reason, reasons, tuple())
    supports = list(Relation('support', reason, conclusion) for reason in reasons)
    return Argument(claims=[conclusion, *reasons_claims], relations=[*supports])

@hasl1_grammar.rule('reasons', [RuleRef('reason-list'), Literal('and'), RuleRef('reason')])
def hasl1_reasons(reasons, conj, reason):
    return (*reasons, reason)

@hasl1_grammar.rule('reason-list', [RuleRef('reason-list'), Literal(','), RuleRef('reason')])
def hasl1_reasonlist_recursive(reasons, conj, reason):
    return (*reasons, reason)

@hasl1_grammar.rule('reason-list', [RuleRef('reason')])
def hasl1_reasonlist_base_case(reason):
    return (reason,)

@hasl1_grammar.rule('reason', [Literal('because'), RuleRef('minor-claims')])
def hasl1_reason(because, claims):
    return claims


@hasl1_grammar.rule('minor-argument', [RuleRef('minor-claim')])
def hasl1_minor_claim(minor):
    """a"""
    return Argument(claims=[minor])

@hasl1_grammar.rule('major-argument', [RuleRef('major-claim')])
def hasl1_major_claim(major):
    """A"""
    return Argument(claims=[major])


@hasl1_grammar.rule('minor-argument', [RuleRef('minor-argument'), Literal('but'), RuleRef('minor-argument')])
def hasl1_attack_minor(conclusion, but, minor):
    """a *- b but a can also be argued"""
    attacks = [Relation('attack', minor.roots, conclusion.root)]
    return Argument(claims=[*conclusion.claims, *minor.claims], relations=[*conclusion.relations, *minor.relations, *attacks])

# def hasl1_attack_minor(conclusion, but, minor):
#     """a *- b but a can also be argued"""
#     merged = (conclusion + minor).consolidate()
#     if merged.mapping[conclusion.root].counters(merged.mapping[minor.root]):
#         attacks = [
#             Relation('attack', [minor.root], conclusion.root),
#             Relation('attack', [conclusion.root], minor.root)
#         ]
#     else:
#         attacks = [
#             Relation('attack', [minor.root], conclusion.root),
#         ]
#     return Argument(claims=[*conclusion.claims, *minor.claims], relations=[*conclusion.relations, *minor.relations, *attacks])


@hasl1_grammar.rule('major-argument', [RuleRef('major-argument'), Literal('but'), RuleRef('argument')])
def hasl1_attack_major(conclusion, but, minor):
    """A *- b but A can also be argued"""
    assert len(conclusion.roots) == 1, 'Attacked claim has multiple root claims'
    attack = Relation('attack', minor.roots, conclusion.root)
    return Argument(claims=[*conclusion.claims, *minor.claims], relations=[*conclusion.relations, *minor.relations, attack])

###
### Enthymeme
###

class MajorClaim(Claim):
    def __init__(self, *args, conditions=tuple(), **kwargs):
        super().__init__(*args, **kwargs)
        self.conditions = tuple(conditions)

    def __str__(self):
        return super().__str__() + ' if ' + english.join(self.conditions)

    def update(self, mapping):
        return MajorClaim(mapping[self.subj], mapping[self.verb], mapping[self.obj],
            negated=self.negated,
            assumed=self.assumed,
            conditions=tuple(condition.update(mapping) for condition in self.conditions))

@hasl1_grammar.rule('minor-claim', [RuleRef('instance'), Tag('VBZ'), RuleRef('object')])
def hasl1_minor_claim_vbz_obj(subj, verb, obj):
    return Claim(subj, verb, obj)

@hasl1_grammar.rule('minor-claim', [RuleRef('instance'), Tag('MD'), Tag('VB')])
def hasl1_minor_claim_md_vb(subj, verb, obj):
    return Claim(subj, verb, obj)

@hasl1_grammar.rule('major-claim', [RuleRef('prototype-sg'), Tag('VBZ'), RuleRef('object')])
def hasl1_major_claim_vbp_obj(cond, verb, obj):
    """Parse major claim as rule: a man is mortal"""
    subj = Entity()
    return MajorClaim(subj, singular_verb(verb), obj, conditions=(Claim(subj, Span(None, None, ['is']), cond),))

@hasl1_grammar.rule('major-claim', [RuleRef('prototype-pl'), Tag('VBP'), RuleRef('object')])
def hasl1_major_claim_vbp_obj(cond, verb, obj):
    """Parse major claim as rule: men are mortal"""
    subj = Entity()
    return MajorClaim(subj, singular_verb(verb), obj, conditions=(Claim(subj, Span(None, None, ['is']), cond),))

@hasl1_grammar.rule('major-claim', [RuleRef('prototype-sg'), Tag('MD'), RuleRef('ability')])
def hasl1_major_claim_mb_vb(cond, verb, obj):
    """Parse major claim as rule: a bird can fly"""
    subj = Entity()
    return MajorClaim(subj, singular_verb(verb), obj, conditions=(Claim(subj, Span(None, None, ['is']), cond),))

@hasl1_grammar.rule('major-claim', [RuleRef('prototype-pl'), Tag('MD'), RuleRef('ability')])
def hasl1_major_claim_mb_vb(cond, verb, obj):
    """Parse major claim as rule: birds can fly"""
    subj = Entity()
    return MajorClaim(subj, singular_verb(verb), obj, conditions=(Claim(subj, Span(None, None, ['is']), cond),))

@hasl1_grammar.rule('major-claim', [RuleRef('prototype-pl'), Tag('VBP'), RuleRef('adverbs'), RuleRef('object')])
def hasl1_negated_major_claim_vbp_obj(cond, verb, neg, obj):
    """Parse major claim as rule: men are not mortal"""
    subj = Entity()
    return MajorClaim(subj, singular_verb(verb), obj, conditions=(Claim(subj, Span(None, None, ['is']), cond, negated=True),))

@hasl1_grammar.rule('major-claim', [RuleRef('prototype-pl'), Tag('MD'), RuleRef('adverbs'), RuleRef('ability')])
def hasl1_negated_major_claim_mb_vb(cond, verb, neg, obj):
    """Parse major claim as rule: birds can not fly"""
    subj = Entity()
    return MajorClaim(subj, singular_verb(verb), obj, conditions=(Claim(subj, Span(None, None, ['is']), cond, negated=True),))

@hasl1_grammar.rule('major-claim', [RuleRef('prototype-sg'), Tag('MD'), RuleRef('adverbs'), RuleRef('ability')])
def hasl1_negated_major_claim_mb_vb(cond, verb, neg, obj):
    """Parse major claim as rule: a bird can not fly"""
    subj = Entity()
    return MajorClaim(subj, singular_verb(verb), obj, conditions=(Claim(subj, Span(None, None, ['is']), cond, negated=True),))

##
## Real enthymeme resolution rules
##

@hasl1_grammar.rule('minor-argument', [RuleRef('minor-claim'), Literal('because'), RuleRef('major-argument')])
def hasl1_support_major_missing_minor(conclusion, because, major):
    minors = [Claim(conclusion.subj, condition.verb, condition.obj, negated=condition.negated, assumed=True) for condition in major.root.conditions]
    support = Relation('support', minors, conclusion)
    warrant = Relation('support', [major.root], support)
    return Argument(claims=[conclusion, *major.claims, *minors], relations=[*major.relations, support, warrant])


@hasl1_grammar.rule('minor-argument', [RuleRef('minor-claim'), Literal('because'), RuleRef('minor-arguments')])
def hasl1_support_major_missing_major(conclusion, because, minors):
    subj = Entity()
    conditions = [Claim(subj, minor.verb, minor.obj, negated=minor.negated, assumed=True) for minor in minors.roots]
    major = MajorClaim(subj, conclusion.verb, conclusion.obj, negated=conclusion.negated, conditions=tuple(conditions), assumed=True)
    support = Relation('support', minors.roots, conclusion)
    warrant = Relation('support', [major], support)
    return Argument(claims=[major, conclusion, *minors.claims], relations=[*minors.relations, support, warrant])


@hasl1_grammar.rule('minor-argument', [RuleRef('minor-claim-list'), Literal('and'), RuleRef('major-argument')])
def hasl1_support_major_missing_conclusion(minors, conj, major):
    subj = minors[0].subj
    conclusion = Claim(subj, major.root.verb, major.root.obj, negated=major.root.negated, assumed=True)
    expected_minors = [Claim(subj, condition.verb, condition.obj, negated=condition.negated, assumed=True) for condition in major.root.conditions]
    support = Relation('support', [*minors, *expected_minors], conclusion)
    warrant = Relation('support', [major.root], support)
    return Argument(claims=[*minors, *expected_minors, *major.claims, conclusion], relations=[*major.relations, support, warrant])

"""
> a because (b but c): a<-b; b*-c
Tweety can fly because Tweety is a bird but Tweety is a dog.
Tweety can fly because Tweety is a bird but Tweety is a dog because birds do not have teeth because they have a beak.
-> a because (b but (c because (d because e)))
Conclusie: b but c returnt b.

> (a because b).conclusion but c: a<-b; a*-c
Tweety can fly because Tweety is a bird but Tweety is a penguin because Tweety has these features.
(a because b).conclusion but (c because d).conclusion
Conclusie: a because b returnt a.

en eigenlijk ook nog
a because b but c: (a<-x)<-b & alle bovenstaande varianten?

(a because (b because (c because d)))
"""

# test(parser.Parser(hasl1_grammar, 'sentences'), sentences)

##
## Evaluation
##

# test(parser.Parser(hasl1_grammar, 'sentences'), [
#     'Socrates is mortal because he is a man and men are mortal.',
#     'Socrates is mortal because he is a man.',
#     'Socrates is mortal because men are mortal.',
#     'Socrates is a man and men are mortal.',
# ])

test(parser.Parser(hasl1_grammar, 'sentences'), [
    # 'Tweety can fly because birds can fly but Tweety is a penguin.',
    # 'Tweety can fly because Tweety is a bird but Tweety is a penguin.',
    'Birds can fly but Tweety can not fly because Tweety is a penguin.',
    # 'The object is red because the object appears red to me but it is illuminated by a red light.'
])

# test(parser.Parser(hasl1_grammar, 'sentences'), [
#     'Petersen will not be a Roman Catholic because he is a Swede and a Swede can be taken almost certainly not to be a Roman Catholic because the proportion of Roman Catholic Swedes is less than 2%.'
# ])

# test(parser.Parser(hasl1_grammar, 'sentences'), [
#     'Harry is a British subject because Harry is a man born in Bermuda but Harry has become naturalized.'
# ])