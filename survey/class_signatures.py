"""Every PUBLISHED BINDING of a tree, not every class: name -> what it is and what it points at.

Run on whichever interpreter resolves ``adcp`` to the tree being dumped; the two trees cannot be
imported into one process, which is why this is a dump and not a comparison.

**A SUBCLASS WALK SEES HALF OF UPSTREAM'S SURFACE.** The first version of this module collected
``pydantic.BaseModel`` subclasses, so a module-scope ``X = SomeClass`` was invisible -- and
upstream publishes a great many of those. ``UpdateMediaBuySuccessResponse`` is one: it is not a
class on their side at all, it is a re-export in their hand-written ``aliases.py``, and 298 of
their tests fail on it. 252 further classes of theirs live outside ``domains/`` entirely --
``registry`` 108, ``base`` 78, ``canonical_creative`` 35 -- which a ``domains``-scoped reading
misses as well.

So the unit is the BINDING: every public module-scope name, with

``kind``       ``model`` (a pydantic class), ``enum``, ``class`` (any other), or ``value``
``declared``   whether the name is where the object was DEFINED (``obj.__module__`` agrees), or
               is a re-export of something defined elsewhere
``points_at``  for a re-export, the dotted path of the object it names -- which is what makes
               the join TRANSITIVE: their ``X = SomeClass`` resolves to whatever ``SomeClass``
               resolves to, so a hand-written alias of theirs needs no rule of its own
``fields`` / ``required`` / ``pointer``
               a model's own facts.  ``pointer`` is OUR ``__adcp_schema__`` and is absent on
               theirs, which is why the join reads a module PATH for the document instead.

Nothing here decides a correspondence.  ``survey/name_table.py`` holds the rules.
"""

from __future__ import annotations

import enum as _enum
import importlib
import json
import pkgutil
import sys

import pydantic


def _kind(obj: object) -> str:
    if isinstance(obj, type):
        if issubclass(obj, pydantic.BaseModel):
            return "model"
        if issubclass(obj, _enum.Enum):
            return "enum"
        return "class"
    return "value"


def _where(obj: object) -> str | None:
    """The dotted path an object was DEFINED at, where it has one."""
    module = getattr(obj, "__module__", None)
    name = getattr(obj, "__qualname__", None) or getattr(obj, "__name__", None)
    return f"{module}.{name}" if module and name else None


def dump() -> dict[str, dict]:
    out: dict[str, dict] = {}
    #: **``_schemas`` AND NEVER THE FACADE** (the owner's reading, measured: with
    #: ``legacy_names``, ``_adapter`` and ``compat`` reduced to docstrings,
    #: ``import adcp.types._schemas`` is OK and a generated module still resolves, so
    #: ``_schemas`` has NO dependency on the alias layer).  ``adcp.types`` is the FACADE
    #: whose whole job is to resolve a name THROUGH that layer, so importing it during
    #: generation asks the layer we are about to write what it currently says -- which is
    #: the circular reasoning, and is what made this module report 1,802 of 1,817 words
    #: redundant.  Reflection is the right tool; the facade is the wrong object.
    root = importlib.import_module("adcp.types._schemas")
    modules = [root]
    for found in pkgutil.walk_packages(root.__path__, "adcp.types._schemas."):
        try:
            modules.append(importlib.import_module(found.name))
        except Exception:  # noqa: BLE001 -- an unimportable module is another row's finding
            continue
    for module in modules:
        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            kind = _kind(obj)
            defined = _where(obj)
            row: dict = {
                "name": name,
                "module": module.__name__,
                "kind": kind,
                "declared": bool(defined and defined == f"{module.__name__}.{name}"),
                "points_at": defined,
                "fields": [],
                "required": [],
                "pointer": None,
            }
            if kind == "model":
                try:
                    fields = obj.model_fields  # type: ignore[union-attr]
                except Exception:  # noqa: BLE001
                    fields = {}
                row["fields"] = sorted(fields)
                row["required"] = sorted(k for k, v in fields.items() if v.is_required())
                ref = getattr(obj, "__adcp_schema__", None)
                row["pointer"] = f"{ref.document}{ref.pointer}" if ref is not None else None
            out.setdefault(f"{module.__name__}.{name}", row)
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    rows = dump()
    with open(argv[0], "w") as handle:
        json.dump(rows, handle)
    kinds: dict[str, int] = {}
    reexports = 0
    for row in rows.values():
        kinds[row["kind"]] = kinds.get(row["kind"], 0) + 1
        reexports += not row["declared"]
    print(f"{len(rows)} bindings -> {argv[0]}")
    print(f"   by kind    : {kinds}")
    print(f"   re-exports : {reexports}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
