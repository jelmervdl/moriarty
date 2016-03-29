from parser import Rule, RuleRef, Literal
import re


class SyntaxError(Exception):
    pass


class ParseError(Exception):
    pass


def parse_grammar(fh):
    rules = set()
    examples = []

    for n, line in enumerate(fh):
        try:
            if line.strip() == "" or line.strip()[0] == ";":
                continue
            elif line[0] == "[":
                examples.append(re.sub(r"\[|\]", "", line.strip()))
            else:
                rules.update(parse_rule(line.strip()))
        except SyntaxError as e:
            raise ParseError("Cannot parse line {}: '{}'".format(n, line.strip()), e)
    
    return rules, examples


def parse_rule(line):
    rules = set()

    match = re.match(r"^\s*(?P<rule>\w+)\s*:(?P<antecedent>.*)\s*$", line)
    if not match:
        raise SyntaxError("Cannot match rule structure")

    name = match.group("rule")

    if match.group("antecedent") == "":
        rules.add(Rule(name, []))
    else:
        for antecedent in match.group("antecedent").split("|"):
            impl_antecedent = parse_antecedent(antecedent.strip())
            impl = Rule(name, impl_antecedent)
            rules.add(impl)

    return rules


def parse_antecedent(line):
    parts = []
    for word in line.split():
        if word[0] == '"' and word[-1] == '"':
            parts.append(Literal(word[1:-1]))
        elif word.isupper():
            parts.append(RuleRef(word))
        else:
            raise SyntaxError("Cannot parse word '{}'".format(word))
    return parts

