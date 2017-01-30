from parser import Rule, RuleRef, Literal, Symbol, State, passthru


class NameParser(Symbol):
    def test(self, literal: str, position: int, state: State) -> bool:
        return literal[0].isupper()


grammar = {
    Rule("NAME", [NameParser()], passthru),
    
    Rule("NAMES", [RuleRef("NAME_"), Literal("and"), RuleRef("NAME")],
        lambda state, data: data[0] + [data[2]]),
    
    Rule("NAME_", [RuleRef("NAME")],
        lambda state, data: [data[0]]),

    Rule("NAME_", [RuleRef("NAME"), Literal(","), RuleRef("NAME_")],
        lambda state, data: [data[0]] + data[2])
}