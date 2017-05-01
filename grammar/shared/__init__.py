from grammar.shared import prototype, instance, category, verb, negation

grammar = prototype.grammar \
    | instance.grammar \
    | category.grammar \
    | verb.grammar \
    | negation.grammar
