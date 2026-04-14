import re


_snake_pattern_1 = re.compile(r"(.)([A-Z][a-z]+)")
_snake_pattern_2 = re.compile(r"([a-z0-9])([A-Z])")


def to_snake(name: str) -> str:
    s = _snake_pattern_1.sub(r"\1_\2", name)
    s = _snake_pattern_2.sub(r"\1_\2", s)
    return s.lower()


def to_pascal(name: str) -> str:
    return "".join(part.capitalize() for part in to_snake(name).split("_") if part)


def pluralize(name: str) -> str:
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    if name.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    return name + "s"
