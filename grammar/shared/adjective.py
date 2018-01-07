import re
from parser import Rule, passthru
from grammar.shared.keywords import Expression


grammar = {
    Rule("ADJECTIVE", [Expression(r".*")], passthru)
}