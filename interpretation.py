from typing import Any, Dict, Set
from argumentation import Argument
import parser

class Interpretation(object):
    _current = list()

    def __init__(self, argument: Argument = Argument(), instances: Dict['Instance', Set['Instance']] = {}, local: Any = None):
        self.argument = argument
        self.instances = instances
        self.local = local

    def __add__(self, other: 'Interpretation') -> 'Interpretation':
        
        # Merge the instances of this and the other Interpretation
        instances = dict(self.instances)
        for other_instance, other_occurrences in other.instances.items():
            merged = False

            # Check for all known instances whether they could be the same as
            # the other Interpretation's instance
            for instance in instances.keys():
                # If that is the case, update our instance and add the other's
                # instance to the list of occurrences
                if instance.could_be(other_instance):
                    merged_instance = instance.replace(other_instance)
                    instances[merged_instance] = instances[instance] | {merged_instance} | other_occurrences
                    del instances[instance]
                    merged = True
                    break

            # if it is new, just copy it to our table
            if not merged:
                instances[other_instance] = other_occurrences

        return Interpretation(
            argument = self.argument | other.argument,
            instances = instances,
            local = other.local)

    def __str__(self) -> str:
        return str(self.argument)

    def __repr__(self) -> str:
        return "Interpretation(argument={argument!r} instances={instances!r} local={local!r})".format(**self.__dict__)

    def __enter__(self):
        print("enter {}".format(hash(self)))
        self._current.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("exit {}".format(hash(self)))
        self._current.pop()

    @classmethod
    def current(cls):
        return cls._current[-1] if len(cls._current) > 0 else None

    def find_instance(self, instance):
        # print("Searching for {}".format(hash(instance)))
        for full_instance, occurrences in self.instances.items():
            if instance in occurrences:
                return full_instance
        return None


class Symbol(parser.Symbol):
    def finish(self, literal: str, state: parser.State):
        return Interpretation(local=literal)


class Literal(parser.Literal):
    def finish(self, literal: str, state: parser.State):
        return Interpretation(local=literal)
