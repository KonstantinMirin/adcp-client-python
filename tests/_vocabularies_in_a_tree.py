"""Which CLASS OBJECTS a tree carries for each vocabulary named on stdin.

**A SCRIPT and not a test, run as a child process**, for ``tests/_imports_a_tree.py``'s
reason exactly: the obligation ranges over the tree a FRESH run emits
(``docs/plan/architecture.md``, "A check may not be downstream of its own precondition"),
an emitted module resolves ``adcp.types.constraints`` by an ABSOLUTE name, and a fresh
tree imported beside the committed one would be graded against the committed alias
module.  One interpreter, one ``adcp``, and the tree it imports is the one the compiler
just produced.

**CLASS OBJECTS and not names, because identity is what §3a is about.**  The defect is
that "one protocol concept" becomes "several Python types that are not interchangeable",
and two modules can bind one NAME to two classes -- measured on the committed tree:
``UpdateFrequency`` and ``PricingModel`` each name two different classes.  So the question
is how many distinct objects carry a vocabulary, which only an import can answer; an AST
census over the text would count two declarations of one name as two and two names of one
class as two, and neither is the property.

stdin: a JSON list of vocabularies, each a list of member VALUES in order.
stdout: a JSON object ``{"carriers": [[<index>, <count>, [<qualified name>, ...]], ...],
"modules": N}``, one entry per input vocabulary, in input order.
"""

from __future__ import annotations

import enum
import importlib
import json
import pkgutil
import sys


def main() -> int:
    asked = [tuple(v) for v in json.load(sys.stdin)]

    import adcp.types._schemas as pkg

    names = sorted(
        info.name
        for info in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + ".")
        if not info.ispkg
    )
    # ``enum.Enum`` and not ``StrEnum``: §5's ``enum`` row reads the base off the members,
    # so an integer vocabulary is an ``IntEnum``, and a census naming one base would miss
    # the three the bundle states.
    found: dict[tuple[object, ...], dict[int, str]] = {}
    modules = 0
    for name in names:
        try:
            module = importlib.import_module(name)
        except Exception:  # reported by the import obligation, not here
            continue
        modules += 1
        for value in vars(module).values():
            if not (isinstance(value, type) and issubclass(value, enum.Enum)):
                continue
            # ``__members__`` is the class's own mapping and carries an ALIAS under its
            # own key, which is right for this question: two values that spell one member
            # name render as a ``Literal`` and no class at all (§5's ``enum`` row), so a
            # class here has one member per value by construction.
            key = tuple(member.value for member in value.__members__.values())
            # Keyed by ``id`` so one class reached through two modules' namespaces is ONE
            # carrier -- which is exactly the property §1's one-import-path rule gives it
            # and what the gate is asking about.
            found.setdefault(key, {})[id(value)] = f"{value.__module__}.{value.__qualname__}"

    carriers = []
    for i, vocabulary in enumerate(asked):
        held = found.get(vocabulary, {})
        carriers.append([i, len(held), sorted(held.values())])
    json.dump({"carriers": carriers, "modules": modules}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
