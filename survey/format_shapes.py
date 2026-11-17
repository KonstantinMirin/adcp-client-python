"""Every ``format`` the bundle states, grouped by the SHAPE of the node that states it.

    PYTHONPATH=.:src ./.venv/bin/python -m survey format_shapes --bundle schemas/cache/3.2

**THIS IS STEP ONE OF THE ALGORITHM, AND IT EXISTS BECAUSE IT WAS SKIPPED.**  The owner's
statement of the design, which has not changed since the beginning: *"survey the types,
then come up with the reference for each, then use them everywhere. That's how URLs came
to be."*  On 2026-11-17 ``format: email`` was wired into ``codegen.lower.scalars``'s
``FORMAT_TYPES`` with a guessed reference and no survey, and both halves of that were
wrong in ways no other instrument reports:

* the reference was a CONSTANT, ``Annotated[str, Field(pattern=r"@")]``.  52 of the
  bundle's 275 email nodes state a ``maxLength`` beside the format and 1 states a
  ``minLength`` too, so a constant carrier drops a fact the document states at 53 of
  them -- the same defect as ``adcp-client-python-rt7v``, committed the same day it was
  filed.
* ``URL_FORMATS`` is derived by "does the chooser answer inside the alias module's
  namespace", which was a PROXY for "is a URL type" and held only while ``uri`` was the
  one chooser that did.  The new entry joined that set silently, so ``email`` was handed
  to ``selects_a_url_type`` -- the URL rule -- and refused selection at every
  bound-bearing node.  Three shipped fields then accepted ``'!!NOT-VALID!!'``.

``./check`` cannot see either: the compiler emitted exactly what the table told it, and
both numbers it prints were unmoved throughout.  What shows it is the shape census,
which is this module.

**WHAT A SHAPE IS, and why the grouping is the whole answer.**  A node's shape is the
sorted tuple of the keywords it states about an instance, with the annotation keywords
dropped -- ``description``, ``title``, ``$comment``, ``examples``, ``x-entity`` state
nothing an annotation must carry, and ``format`` itself is the key being grouped.  So a
format whose nodes have ONE shape can take one carrier, and a format with more than one
needs a carrier that is a FUNCTION OF THE NODE.  ``constraints.url_type`` is that
function and always was: it reads the node's own ``pattern`` and answers ``AdCPUrl`` or
``HostedUrl``.  A table entry that ignores its ``node`` argument is a claim that the
format's nodes are uniform, and this module is where that claim is checked.

**NON-SCHEMA POSITIONS ARE EXCLUDED, measured.**  A walk that descends into ``examples``
counts annotation DATA as a constraint: before this exclusion the same walk reported 21
``YYYYMMDD`` nodes, all of them inside
``core/catalog-field-mapping.json#/examples/1/data``, and ``YYYYMMDD`` is not a JSON
Schema format at all.  ``default``, ``const`` and ``enum`` carry instance values for the
same reason, and ``x-`` is vendor data.

**IT READS AND IT DOES NOT RUN**, which is ``survey/causes.py``'s contract and the
reason both live here: the bundle is the input, the shapes are a grouping of it, and
nothing is emitted, compiled or validated to produce the table.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any

#: Keywords that state nothing about an instance, so two nodes differing only in one of
#: them have the same shape.  ``format`` is the key being grouped and is dropped with
#: them.
_ANNOTATION = frozenset(
    {"description", "title", "format", "$comment", "examples", "example", "x-entity"}
)

#: Pointer segments under which a ``format`` is DATA and not an assertion: an example,
#: a default, a pinned value, an enumerated member, or vendor metadata.
_NON_SCHEMA = ("/examples", "/example", "/default", "/const", "/enum", "/x-")


def shapes(bundle_dir: Path) -> dict[str, collections.Counter[tuple[str, ...]]]:
    """``format`` -> the shapes of the nodes stating it -> how many nodes.

    Every ``.json`` under ``bundle_dir`` except ``bundled/``, which holds the
    dereferenced projections and would count one stating node once per path that
    reaches it.
    """
    per: dict[str, collections.Counter[tuple[str, ...]]] = collections.defaultdict(
        collections.Counter
    )
    for path in sorted(bundle_dir.rglob("*.json")):
        if "bundled" in path.parts:
            continue
        try:
            document = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for fmt, shape in _stated(document):
            per[fmt][shape] += 1
    return dict(per)


def _stated(node: Any, pointer: str = "#") -> list[tuple[str, tuple[str, ...]]]:
    """Every ``(format, shape)`` the subtree states, by a plain recursive walk."""
    out: list[tuple[str, tuple[str, ...]]] = []
    if isinstance(node, dict):
        fmt = node.get("format")
        if isinstance(fmt, str) and not any(seg in pointer for seg in _NON_SCHEMA):
            out.append((fmt, tuple(sorted(k for k in node if k not in _ANNOTATION))))
        for key, value in node.items():
            out.extend(_stated(value, f"{pointer}/{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            out.extend(_stated(value, f"{pointer}/{index}"))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True, help="the bundle directory")
    parser.add_argument("--json", type=Path, help="write the census here as JSON too")
    args = parser.parse_args(argv)

    census = shapes(args.bundle)
    try:
        from codegen.lower.scalars import FORMAT_TYPES, URL_FORMATS

        handled, url = set(FORMAT_TYPES), set(URL_FORMATS)
    except ImportError:  # the census is readable without the compiler on the path
        handled, url = set(), set()

    rows = sorted(census.items(), key=lambda kv: -sum(kv[1].values()))
    print(f"{len(rows)} formats stated in {args.bundle}\n")
    for fmt, counter in rows:
        total = sum(counter.values())
        state = "selects a type" if fmt in handled else "rides as json_schema_extra"
        print(f"{fmt}  —  {total} nodes, {len(counter)} shape(s), {state}")
        if fmt in url:
            print("    (a URL format: the carrier is one of the two URL carriers)")
        for shape, count in counter.most_common():
            print(f"    {count:5d}  {shape or '(format alone)'}")
        print()

    #: **THE CENSUS IS THE OUTPUT AND THERE IS NO VERDICT HERE**, which took two
    #: attempts to get right.  The first flagged "more than one shape and a type is
    #: selected" and cried wolf on ``uri``, whose eight shapes ARE handled --
    #: ``url_type`` reads the node and ``selects_a_url_type`` declines where the carrier
    #: cannot state a fact.  The second asked whether the chooser ignores its node, and
    #: cried wolf on ``email``, whose carrier IS constant and whose facts are composed
    #: beside it (``scalars.lower``'s ``ir.Decided(TypeRef(selected), constraints)``).
    #:
    #: Whether a fact is DROPPED is a property of the lowering path, which a read-only
    #: census cannot see.  So this module reports the shapes and names the question; the
    #: answer is read in ``codegen/lower/scalars.py``.  An instrument that guesses a
    #: verdict is one its reader learns to discount.
    multi = sorted(f for f, c in census.items() if f in handled and len(c) > 1)
    if multi:
        print(
            "formats selecting a type over MORE THAN ONE shape -- for each, read "
            "`scalars.lower`\nand confirm the other shapes' facts are carried, by a "
            "node-function carrier or\nby composition beside a constant one:"
        )
        for fmt in multi:
            print(f"    {fmt}  ({len(census[fmt])} shapes)")
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    fmt: {" ".join(shape) or "-": n for shape, n in counter.items()}
                    for fmt, counter in census.items()
                },
                indent=1,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
