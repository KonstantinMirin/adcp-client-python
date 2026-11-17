"""A bare ``$ref`` position re-emits its target, and the copy diverges from the original.

    PYTHONPATH=.:src ./.venv/bin/python -m survey ref_divergence --bundle schemas/cache/3.2

**WHAT IT MEASURES.**  A document node that states nothing but a ``$ref`` (plus ``title``
and ``description``, which assert nothing) names a type the bundle already has.  §3a's
rule is that such a position RESOLVES to the catalogue entry; what this module asks is
whether it does, by comparing the class emitted AT the referring position against the
class emitted at the TARGET's own node -- branch children, field names, and rules.

**THE CASE THAT PROMPTED IT, and it is one document emitted two ways:**

    media-buy/create-media-buy-response.json#        CreateMediaBuyResponse
        branch children  CreateMediaBuySuccess, CreateMediaBuyError,
                         CreateMediaBuyResponseSubmitted
        the witness      REFUSED

    core/async-response-data.json#/anyOf/18          AdCPAsyncResponseDataCreateMediaBuyResponse
        branch children  (none)
        the witness      ACCEPTED

where the witness is ``{"confirmed_at": …, "errors": [], "media_buy_id": "",
"packages": [], "revision": 1, "status": "submitted"}`` -- a payload the document refuses
on every one of its three branches' ``not`` clauses.  The referring node is a bare
``$ref``; it states no structure of its own.  So one ``oneOf``, three branches, and at one
position the branches are classes that dispatch while at the other what remains is a base
whose fields are all optional and which admits anything the envelope lets through.

**WHY NO EXISTING GATE SEES IT**, which is the reason this module is separate from the
two that come closest:

* ``tests_emit/test_one_node_is_one_declaration.py`` keys on ``(document, pointer)``.
  The two classes key as ``('media-buy/create-media-buy-response.json', '#')`` and
  ``('core/async-response-data.json', '#/anyOf/18')`` -- DIFFERENT keys -- so from its
  view these are two nodes with one class each and there is nothing to report.  It is
  red, for an unrelated shape: 14 nodes where a union's branch classes share one pointer.
* ``tests_emit/duplicates.py`` asks whether two classes are the SAME type, under a
  five-part key, and decides whether they are one subject.  This defect is two classes
  being DIFFERENT.  Sameness has an instrument; divergence has none.

``./check`` cannot see it either: both classes are emitted and neither is refused, so
``emitted 1059 / refused 0`` is unmoved.  ``./verify`` caught SIX of them and only
because a declaration that had been accidentally excusing them was removed --
``core/async-response-data.json``'s ``anyOf``/``UNDERDETERMINED`` entry, whose keyword
the old excusing set matched without testing its kind.

**AND §3a ALREADY DECIDES THIS**, which makes the finding a gap in reach and not in
design.  ``docs/plan/architecture.md``: *"Without the catalogue the compiler reproduces
the defect it was built to escape.  ``datamodel-code-generator`` emitted a type per
position and the result was duplicate classes and unions nobody could name; a
hand-written walk that also emits a type per position arrives at the same place with more
effort.  Faithfulness per node is not consistency across the bundle."*  Measured:
``catalogue.collect_shapes(...).restating()`` covers 87 documents at L2 and 21 at L3, and
``core/async-response-data.json`` is in neither.

**IT READS AND IT DOES NOT RUN**, which is ``survey/causes.py``'s contract: the bundle and
the emitted tree are the inputs, the comparison is a grouping of them, and nothing is
compiled or validated to produce the table.
"""

from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

#: Keywords that assert nothing about an instance, so a node stating only these beside a
#: ``$ref`` states no structure of its own and is a BARE reference.
_INERT = frozenset({"$ref", "title", "description", "$comment", "examples", "example"})


def bare_refs(bundle_dir: Path) -> dict[tuple[str, str], str]:
    """``(document, pointer)`` -> the document a bare ``$ref`` there names."""
    out: dict[tuple[str, str], str] = {}
    for path in sorted(bundle_dir.rglob("*.json")):
        if "bundled" in path.parts:
            continue
        try:
            document = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        name = str(path.relative_to(bundle_dir))
        for pointer, target in _walk(document):
            out[(name, pointer)] = target
    return out


def _walk(node: Any, pointer: str = "#") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and not set(node) - _INERT and "#" not in ref.rsplit("/", 1)[-1]:
            #: A whole-document reference only.  A fragment names a node inside a
            #: document and its own class is the fragment's, not the document root's.
            found.append((pointer, ref.split("/schemas/")[-1].split("/", 1)[-1]))
        for key, value in node.items():
            found.extend(_walk(value, f"{pointer}/{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_walk(value, f"{pointer}/{index}"))
    return found


def emitted() -> dict[tuple[str, str], Any]:
    """``(document, pointer)`` -> the class the tree emits there."""
    import adcp.types._schemas as schemas
    from adcp.types._base import AdCPBaseModel

    out: dict[tuple[str, str], Any] = {}
    for info in pkgutil.walk_packages(schemas.__path__, schemas.__name__ + "."):
        try:
            module = importlib.import_module(info.name)
        except Exception:
            continue
        for value in vars(module).values():
            if not (isinstance(value, type) and issubclass(value, AdCPBaseModel)):
                continue
            if value.__module__ != info.name:
                continue
            ref = getattr(value, "__adcp_schema__", None)
            if ref is not None:
                out.setdefault((ref.document, ref.pointer), value)
    return out


def _shape(cls: Any) -> tuple[int, int, int]:
    """What is compared: branch children, fields, rules.  Counts, not names.

    Names differ BY DESIGN at a referring position -- §4 names a branch for the union
    that declares it -- so comparing names would report every reference as a divergence
    and the table would say nothing.  What must agree is the STRUCTURE.
    """
    return (
        len(cls.__subclasses__()),
        len(getattr(cls, "model_fields", {})),
        len(getattr(cls, "_adcp_rules", ()) or ()),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True, help="the bundle directory")
    parser.add_argument("--json", type=Path, help="write the divergences here too")
    args = parser.parse_args(argv)

    refs, tree = bare_refs(args.bundle), emitted()
    agree, diverge, unemitted = 0, [], 0
    for (document, pointer), target in sorted(refs.items()):
        here = tree.get((document, pointer))
        there = tree.get((target, "#"))
        if here is None or there is None:
            unemitted += 1
            continue
        if _shape(here) == _shape(there):
            agree += 1
        else:
            diverge.append((document, pointer, here, target, there))

    print(f"bare whole-document $ref positions: {len(refs)}")
    print(f"   both ends emitted and AGREE:   {agree}")
    print(f"   both ends emitted and DIVERGE: {len(diverge)}")
    print(f"   one end not a class:           {unemitted}\n")
    for document, pointer, here, target, there in diverge:
        print(f"{document}{pointer}")
        print(f"   emits  {here.__name__:52s} children/fields/rules = {_shape(here)}")
        print(f"   target {target}")
        print(f"          {there.__name__:52s} children/fields/rules = {_shape(there)}")
        print()
    if args.json:
        args.json.write_text(
            json.dumps(
                [
                    {
                        "document": d,
                        "pointer": p,
                        "here": h.__name__,
                        "here_shape": _shape(h),
                        "target": t,
                        "there": o.__name__,
                        "there_shape": _shape(o),
                    }
                    for d, p, h, t, o in diverge
                ],
                indent=1,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
