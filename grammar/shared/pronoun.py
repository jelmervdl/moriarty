from parser import Rule, passthru
from interpretation import Literal

grammar = {
    # Singular
    Rule("PRONOUN", [Literal('he')], passthru),
    Rule("PRONOUN", [Literal('she')], passthru),
    Rule("PRONOUN", [Literal('it')], passthru),

    # Plural
    Rule("PRONOUNS", [Literal('they')], passthru),

    # Undetermined
    Rule("PRONOUN", [Literal('someone')], passthru),
    Rule("PRONOUN", [Literal('something')], passthru),
}