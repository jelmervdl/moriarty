from parser import Rule, Symbol, State, passthru

class AdjectiveParser(Symbol):
    """
    Adjectives typically and on -ly, -able, -ful, -ical, etc. but you also
    have adjectives such as 'red', 'large', 'rich'. On top of that, you can
    convert verbs to adjectives using -ed and -able. So we'll just accept
    anything today :)
    """
    def test(self, literal: str, position: int, state: State) -> bool:
        return True

grammar = {
    Rule("CATEGORY", [AdjectiveParser()], passthru)
}
