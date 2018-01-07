import re
from parser import Rule, passthru
from interpretation import Expression


grammar = {
    Rule("ADJECTIVE", [Expression(r"(?!the)")], passthru)
}