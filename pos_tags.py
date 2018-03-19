import spacy
import english
import traceback

nlp = spacy.load('en', disable=['parser', 'ner', 'textcat'])


class Debug(object):
    def __init__(self):
        self.counter = 0

    def __enter__(self):
        self.counter += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.counter -= 1

    def __call__(self, text):
        if self.counter > 0:
            print(text)

debug = Debug()

def indent(text, prefix='\t'):
    return '\n'.join(prefix + line for line in text.split('\n'))


def unique(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]


class Stamper(object):
    def __init__(self):
        self.seq = 0
        self.attr = '_id_stamp'

    def next(self):
        self.seq += 1
        return self.seq

    def __call__(self, obj):
        if not hasattr(obj, self.attr):
            setattr(obj, self.attr, self.next())
        return getattr(obj, self.attr)

id = Stamper()

def read_id(obj):
    if not hasattr(obj, id.attr):
        raise Exception("Object {!r} has no id yet".format(obj))
    return id(obj)

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

hasl0_sentences = [
    'Socrates is mortal because he is a man and men are mortal.',
    'The object is red because the object appears red but it is illuminated by a red light.',
    'Tweety can fly because he is a bird. He is a bird because he has wings.'
]

premises = [
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


import parser
from parser import Rule, RuleRef, passthru
from pprint import pprint
from functools import reduce
from itertools import chain
from typing import NamedTuple, Tuple, Dict, Any
import operator
import re


class Mapping(object):
    def __init__(self, entries):
        self.entries = dict(entries)
        for key in self.entries.keys():
            while read_id(self.entries[key]) != read_id(self.entries[id(self.entries[key])]):
                self.entries[key] = self.entries[read_id(self.entries[key])]

    def __add__(self, other):
        return Mapping(chain(self.entries.items(), other.entries.items()))

    def __getitem__(self, obj):
        if isinstance(obj, tuple):
            return tuple(self[el] for el in obj)
        if isinstance(obj, list):
            return list(self[el] for el in obj)
        else:
            debug("Looking for {}{!s}: {}".format(id(obj), obj, 'found' if id(obj) in self.entries else 'not found'))
            return self.entries[read_id(obj)] if id(obj) in self.entries else obj

    def __setitem__(self, obj, replacement):
        self.entries[id(obj)] = replacement
        self.entries[id(replacement)] = replacement


class Span(object):
    def __init__(self, start, end, tokens):
        self.start = start
        self.end = end
        self.tokens = tokens

    def __add__(self, other):
        return Span(self.start, other.end, self.tokens + other.tokens)

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


def test(p, sentences):
    for sentence in sentences:
        doc = nlp(sentence)
        print_pos_tags(doc)
        try:
            parses = p.parse(doc)
            print("There are {} parses".format(len(parses)))
            for parse in parses:
                print("Parse:")
                pprint(parse['data'])
                print("Tree:")
                pprint(parse['tree'])

        except parser.ParseError as e:
            print("Failure: {}".format(e))
        print()


class Entity(object):
    def __init__(self, name = None, noun = None, pronoun = None):
        self.name = name
        self.noun = noun
        self.pronoun = pronoun

    def __str__(self):
        if self.name is not None:
            return str(self.name)
        if self.noun is not None:
            return str(self.noun)
        if self.pronoun is not None:
            return str(self.pronoun)
        else:
            return 'something'

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return self.name == other.name \
            and self.noun == other.noun \
            and self.pronoun == other.pronoun

    def __repr__(self):
        return "({} name={name} noun={noun} pronoun={pronoun})".format(id(self), **self.__dict__)

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



class Premise(object):
    def __init__(self, subj, verb, obj, negated=False):
        self.subj = subj
        self.verb = verb
        self.obj = obj
        self.negated = negated

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return "{subj} {verb} {neg}{obj}".format(neg="not " if self.negated else "", **self.__dict__)

    def __repr__(self):
        return "{neg}{subj!r} {verb!r} {obj!r}".format(neg = "not " if self.negated else "", **self.__dict__)

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
        return Premise(mapping[self.subj], mapping[self.verb], mapping[self.obj], self.negated)


class Relation(object):
    arrows = {
        'attack': '~*',
        'support': '~>'
    }

    def __init__(self, type, sources, target):
        self.type = type
        self.sources = tuple(sources)
        self.target = target

    def __str__(self):
        return "({} {} {})".format(' ^ '.join(str(s) for s in self.sources), self.arrows[self.type], self.target)

    def __repr__(self):
        return "{} ({!r}) {} ({!r})".format(self.type, self.sources, self.arrows[self.type], self.target)

    def update(self, mapping):
        return Relation(self.type,
            sources = tuple(mapping[source] for source in self.sources),
            target = mapping[self.target])


class ArgumentData(NamedTuple):
    premises: Tuple[Premise, ...]
    relations: Tuple[Relation, ...]
    
    def __repr__(self):
        return "Premises:\n{}\nRelations:\n{}".format(
            "\n".join(str(p) for p in self.premises),
            "\n".join(str(r) for r in self.relations))


class Argument(ArgumentData):
    def __new__(cls, premises = tuple(), relations = tuple()):
        return super().__new__(cls, tuple(premises), tuple(relations))

    def consolidate(self, mapping):
        def replace(old, new, list):
            old_ids = frozenset(id(el) for el in old)
            for el in list:
                if id(el[1]) in old_ids:
                    el[1] = new

        entities = [[id(entity), entity] for entity in sorted((entity for entity in chain.from_iterable(premise.entities for premise in self.premises) if entity.pos is not None), key=lambda entity: entity.pos)]

        c = len(entities)
        for m, entity in enumerate(entities[:c]):
            for n, other_entity in enumerate(entities[m+1:c], m+1):
                result = other_entity[1].refers_to(entity[1])
                # print("Does {!r} ({}) refer to {!r} ({}): {!r}".format(other_entity[1], id(other_entity[1]), entity[1], id(entity[1]), result))
                if result:
                    merged = entity[1].merge(other_entity[1])
                    entities.append([id(merged), merged])
                    replace((entity[1], other_entity[1]), merged, entities)

        mapping += Mapping(entities)

        entries = [[id(premise), premise] for premise in self.premises]

        # Update all premises with the new entities
        for entry in entries[0:len(entries)]: # to prevent iterating over new items
            updated = entry[1].update(mapping)
            entry[1] = updated
            entries.append([id(updated), updated])

        # Merge all premises that are (or have become) equal
        for m, entry in enumerate(entries):
            for n, other_entry in enumerate(entries[m:], m):
                if entry[1] == other_entry[1]:
                    entries[n][1] = entry[1]

        mapping += Mapping(entries)
        
        relations = []
        for i, relation in enumerate(self.relations):
            updated = relation.update(mapping)
            relations.append(updated)
            mapping[relation] = updated

        return Argument(
            premises=tuple(entry[1] for entry in entries if entry[0] == id(entry[1])),
            relations=tuple(relations)), mapping


class Grammar(object):
    def __init__(self, rules = None):
        self.rules = rules if rules is not None else []

    def __iter__(self):
        return iter(self.rules)

    def __add__(self, other):
        return self.__class__(self.rules + list(other))

    def rule(self, name, symbols):
        rule = Rule(name, symbols)
        self.rules.append(rule)
        def wrapper(callback):
            rule.callback = lambda state, data: callback(*data)
            return callback
        return wrapper


def merge(state, data):
    return reduce(operator.__add__, data)


en_grammar = Grammar([
    Rule('name', [Tag('NNP')], merge),
    Rule('name', [Literal('Tweety')], merge),
    
    Rule('instance', [RuleRef('name')],
        lambda state, data: Entity(name=data[0])),
    Rule('instance', [Tag('PRP')],
        lambda state, data: Entity(pronoun=data[0])),
    Rule('instance', [RuleRef('def-dt'), Tag('NNP?')],
        lambda state, data: Entity(noun=data[0] + data[1])),

    Rule('object', [Tag('NNS?')], merge),
    Rule('object', [Tag('JJ')], merge),
    Rule('object', [Tag('DT'), Tag('NN')], merge),
    Rule('object', [Tag('DT'), Tag('JJ'), Tag('NN')], merge),
    Rule('object', [RuleRef('vbn')], merge),

    Rule('prototype-sg', [RuleRef('indef-dt'), Tag('NN')], merge),
    Rule('prototype-sg', [RuleRef('indef-dt'), Tag('NN'), RuleRef('vbn')], merge),

    Rule('prototype-pl', [Tag('NNS')], merge),
    Rule('prototype-pl', [Tag('NNS'), RuleRef('vbn')], merge),

    Rule('vbn', [Tag('VBN')], passthru),
    Rule('vbn', [Tag('VBN'), RuleRef('prep-phrase')], merge),

    Rule('prep-phrase', [Tag('IN'), Tag('NNP')], merge), # for "In Bermuda"
    Rule('prep-phrase', [Tag('IN'), RuleRef('object')], merge), # for "by a red light"

    Rule('def-dt', [Literal('The')], passthru),
    Rule('def-dt', [Literal('the')], passthru),
    Rule('def-dt', [Literal('this')], passthru),

    Rule('indef-dt', [Literal('a')], passthru),
])

hasl0_grammar = en_grammar + [
    Rule('sentences',   [RuleRef('sentences'), RuleRef('sentence')], lambda state, data: data[0] + data[1]),
    Rule('sentences',   [RuleRef('sentence')], passthru),
    Rule('sentence',    [RuleRef('argument'), Literal('.')], passthru),

    Rule('minor-premise', [RuleRef('instance'), Tag('VBZ'), RuleRef('object')],
        lambda state, data: Premise(data[0], data[1], data[2])),
    Rule('minor-premise', [RuleRef('instance'), Tag('MD'), Tag('VB')],
        lambda state, data: Premise(data[0], data[1], data[2])),
    
    Rule('major-premise', [Tag('NNS'), Tag('VB[PD]'), RuleRef('object')],
        lambda state, data: Premise(data[0], data[1], data[2])),
    Rule('major-premise', [Tag('NNS'), Tag('MD'), Tag('VB')],
        lambda state, data: Premise(data[0], data[1], data[2])),
    
    Rule('premise', [RuleRef('major-premise')], passthru),
    Rule('premise', [RuleRef('minor-premise')], passthru),


    Rule('minor-premises', [RuleRef('minor-premise')],
        lambda state, data: (data[0],)),
    Rule('minor-premises', [RuleRef('minor-premise-list'), Literal('and'), RuleRef('minor-premise')],
        lambda state, data: (*data[0], data[2])),
    Rule('minor-premise-list', [RuleRef('minor-premise')],
        lambda state, data: (data[0],)),
    Rule('minor-premise-list', [RuleRef('minor-premise-list'), Literal(','), RuleRef('minor-premise')],
        lambda state, data: (*data[0], data[2])),

    Rule('argument',    [RuleRef('support')], passthru),
    Rule('argument',    [RuleRef('attack')], passthru),
    Rule('argument',    [RuleRef('warranted-support')], passthru),
    Rule('argument',    [RuleRef('undercutter')], passthru),
]

@hasl0_grammar.rule('support', [RuleRef('premise'), Literal('because'), RuleRef('minor-premises')])
def support(conclusion, marker, minors):
    """a <- b+"""
    return Argument(premises=(conclusion,) + minors, relations=(Relation('support', minors, conclusion),))

@hasl0_grammar.rule('attack', [RuleRef('premise'), Literal('but'), RuleRef('minor-premises')])
def support(conclusion, marker, minors):
    """a *- b+"""
    return Argument(premises=(conclusion, *minors), relations=[Relation('attack', minors, conclusion)])

@hasl0_grammar.rule('warranted-support', [RuleRef('premise'), Literal('because'), RuleRef('minor-premise-list'), Literal('and'), RuleRef('major-premise')])
def warranted_support_minor_major(conclusion, marker, minors, conj, major):
    """(a <- b+) <- c"""
    support = Relation('support', minors, conclusion)
    warrant = Relation('support', (major,), support)
    return Argument(premises=(conclusion, *minors, major), relations=(support, warrant))

@hasl0_grammar.rule('warranted-support', [RuleRef('premise'), Literal('because'), RuleRef('major-premise'), Literal('and'), RuleRef('minor-premises')])
def warranted_support_major_minor(conclusion, marker, major, conj, minors):
    """(a <- c+) <- b"""
    support = Relation('support', minors, conclusion)
    warrant = Relation('support', (major,), support)
    return Argument(premises=(conclusion, major, *minors), relations=(support, warrant))

@hasl0_grammar.rule('warranted-attack', [RuleRef('premise'), Literal('because'), RuleRef('minor-premise-list'), Literal('and'), RuleRef('major-premise')])
def warranted_attack_minor_major(conclusion, marker, minors, conj, major):
    """(a <- b+) <- c"""
    attack = Relation('attack', minors, conclusion)
    warrant = Relation('support', (major,), attack)
    return Argument(premises=(conclusion, *minors, major), relations=(attack, warrant))

@hasl0_grammar.rule('warranted-attack', [RuleRef('premise'), Literal('because'), RuleRef('major-premise'), Literal('and'), RuleRef('minor-premises')])
def warranted_attack_major_minor(conclusion, marker, major, conj, minors):
    """(a <- c+) <- b"""
    attack = Relation('attack', minors, conclusion)
    warrant = Relation('support', (major,), attack)
    return Argument(premises=(conclusion, major, *minors), relations=(attack, warrant))


"""
> (a because b) but c: (a<-b)<-c
Tweety is a bird because Tweety can fly but planes can also fly
Tweety is a bird because Tweety can fly but Tweety was thrown
Conclusie: zinloos om iets achter te zetten -> geval apart. Also de enige manier om deze te construeren.
"""
@hasl0_grammar.rule('undercutter', [RuleRef('premise'), Literal('because'), RuleRef('minor-premises'), Literal('but'), RuleRef('premise')])
def undercutter(conclusion, because, minors, but, attack):
    """(a <- b+) *- c (c can be both minor and major)"""
    support = Relation('support', minors, conclusion)
    undercutter = Relation('attack', (attack,), support)
    return Argument(premises=(conclusion, *minors, attack), relations=(support, undercutter))

###
### Recursion
###

class HASL1Grammar(Grammar):
    def rule(self, name, symbols):
        rule = Rule(name, symbols)
        self.rules.append(rule)
        def wrapper(callback):
            rule.callback = lambda state, data: callback(*data).consolidate()
            return callback
        return wrapper


class StateData(NamedTuple):
    argument: Argument
    premise: Premise # salient premise
    mapping: Mapping

    def __repr__(self):
        return "Salient premise:\n{}\nArgument:\n{}".format(indent(str(self.premise), "  "), indent(repr(self.argument), "  "))

    

class State(StateData):
    def __new__(cls, argument = Argument(), premise = None, mapping = Mapping([])):
        return super().__new__(cls, argument, premise, mapping)
    
    def __add__(self, other):
        other_argument = other.argument if isinstance(other, State) else other
        return State(
            Argument(
                premises = self.argument.premises + other_argument.premises,
                relations = self.argument.relations + other_argument.relations,
            ),
            self.premise, # is the first "sentence" the salient premise?
            (self.mapping + other.mapping) if isinstance(other, State) else self.mapping
        )

    def consolidate(self):
        argument, mapping = self.argument.consolidate(self.mapping)
        return State(argument, mapping[self.premise], mapping)


hasl1_grammar = HASL1Grammar([]) + en_grammar + [
    Rule('sentences',   [RuleRef('sentence'), RuleRef('sentence')], lambda state, data: (data[0] + data[1]).consolidate()),
    Rule('sentences',   [RuleRef('sentence')], passthru),
    Rule('sentence',    [RuleRef('argument'), Literal('.')], passthru),

    Rule('argument',    [RuleRef('argued-minor-premise')], passthru),
    Rule('argument',    [RuleRef('argued-major-premise')], passthru),
]

@hasl1_grammar.rule('argued-minor-premises', [RuleRef('argued-minor-premise')])
def hasl1_argued_minor_premises_single(minor):
    assert isinstance(minor.premise, Premise)
    return State(premise=(minor.premise,)) + minor

@hasl1_grammar.rule('argued-minor-premises', [RuleRef('minor-premise-list'), Literal('and'), RuleRef('argued-minor-premise')])
def hasl1_argued_minor_premises_multiple(list, conj, minor):
    assert isinstance(minor.premise, Premise)
    return State(premise=(*list.premise, minor.premise)) + list + minor

@hasl1_grammar.rule('minor-premise-list', [RuleRef('minor-premise')])
def hasl1_minor_premises_list_single(minor):
    assert isinstance(minor.premise, Premise)
    return State(premise=(minor.premise,)) + minor

@hasl1_grammar.rule('minor-premise-list', [RuleRef('minor-premise-list'), Literal(','), RuleRef('minor-premise')])
def hasl1_minor_premises_list_multiple(list, conj, minor):
    assert isinstance(minor.premise, Premise)
    return State(premise=(*list.premise, minor.premise)) + list + minor


@hasl1_grammar.rule('minor-premise', [RuleRef('instance'), Tag('VBZ'), Tag('RB'), RuleRef('object')])
def hasl1_minor_premise_vbz_obj(subj, verb, neg, obj):
    premise = Premise(subj, verb, obj, negated=True)
    return State(Argument(premises=(premise,)), premise)

@hasl1_grammar.rule('minor-premise', [RuleRef('instance'), Tag('MD'), Tag('RB'), Tag('VB')])
def hasl1_negated_minor_premise_md_vb(subj, verb, neg, obj):
    premise = Premise(subj, verb, obj, negated=True)
    return State(Argument(premises=(premise,)), premise)

@hasl1_grammar.rule('minor-premise', [RuleRef('instance'), Tag('VB[DZ]'), RuleRef('vbn')])
def hasl1_minor_premise_vbdz_vbn(subj, verb, obj):
    premise = Premise(subj, verb, obj)
    return State(Argument(premises=[premise]), premise)

@hasl1_grammar.rule('argued-minor-premise', [RuleRef('minor-premise'), Literal('because'), RuleRef('argued-minor-premises')])
def hasl1_support_minor(conclusion, because, minors):
    """a <- b+"""
    support = Relation('support', minors.premise, conclusion.premise)
    return conclusion + minors + Argument(relations=(support,))

@hasl1_grammar.rule('argued-major-premise', [RuleRef('major-premise'), Literal('because'), RuleRef('argued-minor-premises')])
def hasl1_support_major(conclusion, because, minors):
    """A <- b+"""
    support = Relation('support', minors.premises, conclusion.premise)
    return conclusion + minors + Argument(relations=(support,))

@hasl1_grammar.rule('argued-minor-premise', [RuleRef('minor-premise'), Literal('because'), RuleRef('major-premise'), Literal('and'), RuleRef('argued-minor-premises')])
def hasl1_warranted_support_major_minor(conclusion, because, major, conj, minors):
    """(a <- c) <- B"""
    support = Relation('support', minors.premise, conclusion.premise)
    warrant = Relation('support', (major.premise,), support)
    return conclusion + major + minors + Argument(relations=(support, warrant))

@hasl1_grammar.rule('argued-minor-premise', [RuleRef('minor-premise'), Literal('because'), RuleRef('minor-premise-list'), Literal('and'), RuleRef('argued-major-premise')])
def hasl1_warranted_support_minor_major(conclusion, because, minors, conj, major):
    """(a <- b) <- C"""
    support = Relation('support', minors.premise, conclusion.premise)
    warrant = Relation('support', (major.premise,), support)
    return conclusion + minors + major + Argument(relations=(support, warrant))

@hasl1_grammar.rule('argued-minor-premise', [RuleRef('minor-premise')])
def hasl1_minor_premise(minor):
    """a"""
    return minor

@hasl1_grammar.rule('argued-major-premise', [RuleRef('major-premise')])
def hasl1_major_premise(major):
    """A"""
    return major


@hasl1_grammar.rule('argued-minor-premise', [RuleRef('argued-minor-premise'), Literal('but'), RuleRef('argued-minor-premise')])
def hasl1_attack_minor(conclusion, but, minor):
    """a *- b but a can also be argued"""
    merged = (conclusion + minor).consolidate()
    if merged.mapping[conclusion.premise].counters(merged.mapping[minor.premise]):
        attacks = (
            Relation('attack', (minor.premise,), conclusion.premise),
            Relation('attack', (conclusion.premise,), minor.premise)
        )
    else:
        attacks = (
            Relation('attack', (minor.premise,), conclusion.premise),
        )
    return conclusion + minor + Argument(relations=attacks)

@hasl1_grammar.rule('argued-major-premise', [RuleRef('argued-major-premise'), Literal('but'), RuleRef('argued-minor-premise')])
def hasl1_attack_major(conclusion, but, minor):
    """A *- b but A can also be argued"""
    attack = Relation('attack', (minor.premise,), conclusion.premise)
    return conclusion + minor + Argument(relations=(attack,))

###
### Enthymeme
###

class MajorPremise(Premise):
    def __init__(self, *args, conditions=tuple(), **kwargs):
        super().__init__(*args, **kwargs)
        self.conditions = tuple(conditions)

    def __str__(self):
        return super().__str__() + ' if ' + english.join(self.conditions)

    def update(self, mapping):
        return MajorPremise(mapping[self.subj], mapping[self.verb], mapping[self.obj],
            negated=self.negated,
            conditions=tuple(condition.update(mapping) for condition in self.conditions))

@hasl1_grammar.rule('minor-premise', [RuleRef('instance'), Tag('VBZ'), RuleRef('object')])
def hasl1_minor_premise_vbz_obj(subj, verb, obj):
    premise = Premise(subj, verb, obj)
    return State(Argument(premises=(premise,)), premise)

@hasl1_grammar.rule('minor-premise', [RuleRef('instance'), Tag('MD'), Tag('VB')])
def hasl1_minor_premise_md_vb(subj, verb, obj):
    premise =Premise(subj, verb, obj)
    return State(Argument(premises=(premise,)), premise)

@hasl1_grammar.rule('major-premise', [RuleRef('prototype-sg'), Tag('VBZ'), RuleRef('object')])
def hasl1_major_premise_vbp_obj(cond, verb, obj):
    """Parse major premise as rule: a man is mortal"""
    subj = Entity()
    conclusion = MajorPremise(subj, verb, obj, conditions=(Premise(subj, Span(None, None, ['is']), cond),))
    return State(Argument(premises=(conclusion,)), conclusion)

@hasl1_grammar.rule('major-premise', [RuleRef('prototype-pl'), Tag('VBP'), RuleRef('object')])
def hasl1_major_premise_vbp_obj(cond, verb, obj):
    """Parse major premise as rule: men are mortal"""
    subj = Entity()
    conclusion = MajorPremise(subj, verb, obj, conditions=(Premise(subj, Span(None, None, ['is']), cond),))
    return State(Argument(premises=(conclusion,)), conclusion)

@hasl1_grammar.rule('major-premise', [RuleRef('prototype-sg'), Tag('MD'), Tag('VB')])
def hasl1_major_premise_mb_vb(cond, verb, obj):
    """Parse major premise as rule: a bird can fly"""
    subj = Entity()
    conclusion = MajorPremise(subj, verb, obj, conditions=(Premise(subj, Span(None, None, ['is']), cond),))
    return State(Argument(premises=(conclusion,)), conclusion)

@hasl1_grammar.rule('major-premise', [RuleRef('prototype-pl'), Tag('MD'), Tag('VB')])
def hasl1_major_premise_mb_vb(cond, verb, obj):
    """Parse major premise as rule: birds can fly"""
    subj = Entity()
    conclusion = MajorPremise(subj, verb, obj, conditions=(Premise(subj, Span(None, None, ['is']), cond),))
    return State(Argument(premises=(conclusion,)), conclusion)

@hasl1_grammar.rule('major-premise', [RuleRef('prototype-pl'), Tag('VBP'), Tag('RB'), RuleRef('object')])
def hasl1_negated_major_premise_vbp_obj(cond, verb, neg, obj):
    """Parse major premise as rule: men are not mortal"""
    subj = Entity()
    conclusion = MajorPremise(subj, verb, obj, conditions=(Premise(subj, Span(None, None, ['is']), cond, negated=True),))
    return State(Argument(premises=(conclusion,)), conclusion)

@hasl1_grammar.rule('major-premise', [RuleRef('prototype-pl'), Tag('MD'), Tag('RB'), Tag('VB')])
def hasl1_negated_major_premise_mb_vb(cond, verb, neg, obj):
    """Parse major premise as rule: birds can not fly"""
    subj = Entity()
    conclusion = MajorPremise(subj, verb, obj, conditions=(Premise(subj, Span(None, None, ['is']), cond, negated=True),))
    return State(Argument(premises=(conclusion,)), conclusion)

@hasl1_grammar.rule('major-premise', [RuleRef('prototype-sg'), Tag('MD'), Tag('RB'), Tag('VB')])
def hasl1_negated_major_premise_mb_vb(cond, verb, neg, obj):
    """Parse major premise as rule: a bird can not fly"""
    subj = Entity()
    conclusion = MajorPremise(subj, verb, obj, conditions=(Premise(subj, Span(None, None, ['is']), cond, negated=True),))
    return State(Argument(premises=(conclusion,)), conclusion)

@hasl1_grammar.rule('argued-minor-premise', [RuleRef('minor-premise'), Literal('because'), RuleRef('argued-major-premise')])
def hasl1_support_major_missing_minor(conclusion, because, major):
    minors = [Premise(conclusion.premise.subj, condition.verb, condition.obj, negated=condition.negated) for condition in major.premise.conditions]
    support = Relation('support', tuple(minors), conclusion.premise)
    warrant = Relation('support', [major.premise], support)
    return conclusion + major + Argument(premises=minors, relations=[support, warrant])


@hasl1_grammar.rule('argued-minor-premise', [RuleRef('minor-premise'), Literal('because'), RuleRef('argued-minor-premises')])
def hasl1_support_major_missing_major(conclusion, because, minors):
    subj = Entity()
    conditions = [Premise(subj, minor.verb, minor.obj) for minor in minors.premise]
    major = MajorPremise(subj, conclusion.premise.verb, conclusion.premise.obj, conditions=tuple(conditions))
    support = Relation('support', minors.premise, conclusion.premise)
    warrant = Relation('support', [major], support)
    return conclusion + minors + Argument(premises=[major], relations=[support, warrant])

@hasl1_grammar.rule('argued-minor-premise', [RuleRef('minor-premise-list'), Literal('and'), RuleRef('argued-major-premise')])
def hasl1_support_major_missing_conclusion(minors, conj, major):
    subj = minors.premise[0].subj
    conclusion = Premise(subj, major.premise.verb, major.premise.obj)
    expected_minors = [Premise(subj, condition.verb, condition.obj, negated=condition.negated) for condition in major.premise.conditions]
    support = Relation('support', [*minors.premise, *expected_minors], conclusion)
    warrant = Relation('support', [major.premise], support)
    return State(premise=conclusion) + minors + major + Argument(premises=[conclusion, *expected_minors], relations=[support, warrant])



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

test(parser.Parser(hasl1_grammar, 'sentences'), sentences)
