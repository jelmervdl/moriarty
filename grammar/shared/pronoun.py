from parser import Rule, Literal, passthru

grammar = {
    # Singular
    Rule("PRONOUN", [Literal('he')], passthru),
    Rule("PRONOUN", [Literal('she')], passthru),
    Rule("PRONOUN", [Literal('it')], passthru),

    # Plural
    Rule("PRONOUNS", [Literal('they')], passthru)
}