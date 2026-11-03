"""Import every module of the tree rooted at ``sys.path[0]`` and resolve every class.

**A SCRIPT and not a test, run as a child process**, which is the whole of why this file
exists.  ``docs/plan/architecture.md`` ("A check may not be downstream of its own
precondition", 2026-10-29) requires the import obligation to range over "the tree a fresh
run EMITS, not the one committed" -- and a fresh tree cannot be imported in the suite's own
interpreter, for a reason that is about the package and not about hygiene: an emitted
module says ``from adcp.types.constraints import StrMatchingA828669D``, an ABSOLUTE name,
so the fresh modules resolve their aliases through whichever ``adcp.types.constraints`` is
already bound.  Importing a fresh tree beside the committed one would therefore grade fresh
classes against the COMMITTED alias module, and a fresh alias the committed module does not
carry is exactly the defect this is here to report.

So the caller writes a whole ``adcp`` package -- hand-written halves copied, generated
halves fresh -- and runs this with that directory first on ``PYTHONPATH``.  One
interpreter, one ``adcp``, and the tree it imports is the one the compiler just produced.

Prints one JSON object on stdout: ``{"modules": N, "classes": N, "failures": [[name,
why], ...]}``.  A failure is REPORTED and never raised, because the obligation is over
every module and the first unimportable one would otherwise hide the rest -- which is the
same shape as the defect the decision names.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import sys
import traceback


def main() -> int:
    from pydantic import BaseModel

    import adcp.types._schemas as pkg

    failures: list[tuple[str, str]] = []
    names = sorted(
        info.name
        for info in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + ".")
        if not info.ispkg
    )
    classes = 0
    for name in names:
        try:
            module = importlib.import_module(name)
        except Exception:  # the failure is the finding
            failures.append((name, traceback.format_exc(limit=3)[-600:]))
            continue
        for value in vars(module).values():
            if (
                isinstance(value, type)
                # ``BaseModel`` and not ``AdCPBaseModel``: a ROOT MODEL is a
                # ``pydantic.RootModel`` and carries no ``AdCPBaseModel`` in its MRO, and
                # an unresolved annotation on one is the same defect read one class over.
                and issubclass(value, BaseModel)
                and value.__module__ == name
            ):
                classes += 1
                try:
                    # ``model_json_schema()`` is what asks the second half: an unresolved
                    # forward reference survives the import and fails only when pydantic
                    # is asked to build the schema.
                    value.model_json_schema()
                except Exception as why:  # the failure is the finding
                    failures.append((f"{name}.{value.__name__}", str(why)[:400]))
    json.dump({"modules": len(names), "classes": classes, "failures": failures}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
