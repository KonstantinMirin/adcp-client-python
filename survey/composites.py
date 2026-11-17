"""Every position that COMPOSES a ``$ref``, grouped by what its own text adds.

    PYTHONPATH=.:src ./.venv/bin/python -m survey.composites --bundle schemas/cache/3.2

**THIS IS §3a's COMPOSITE LAYER READ OUT, AND IT EXISTS BECAUSE THE LAYER HAD NO KEY.**
§3a's sentence *"THE KEY IS THE VALUE LIST, not the structural identity §3a named"* stood
unqualified until 2026-11-17. Read as §3a's rule rather than as L0's it says every
layer's entry key is a value list -- and an object type has no value list, so L2 and L3
were left with no identity at all. The owner's statement of the design, unchanged since
the beginning: *"We find the primitive types, composite types, more composite types, and
make sure that we reuse them as we create the types structure."* The primitive layers got
their reference. The composite layer did not, and this module is what that is worth.

**EVERY READING HERE IS THE COMPILER'S OWN, AND THE FIRST DRAFT OF THIS MODULE PROVED WHY
THAT IS NOT A STYLE PREFERENCE.** It hand-rolled three things the harness already
declares, and each was wrong in a way that changed the answer:

* the DOCUMENT SET was ``bundle_dir.rglob("*.json")`` minus ``bundled/``. The compiler's
  screen is :func:`codegen.catalogue.stating`, which is :func:`bundle.portable` less the
  non-home members of a repeated document. Measured: the hand-rolled walk read **367
  documents, 125 of them not in the compiler's 1,054** -- the ``mcp/`` and ``profiles/``
  projections, which no layer collects from. Every count was inflated by them.
* the WALK was ``for key, value in node.items()``, which descends into ``examples``,
  ``const`` and ``default`` -- instance DATA read as schema. :func:`bundle.nodes_at` is
  the compiler's walk and descends the ``DESCENDS`` table and nothing else.
* the POSITION KIND was a string test against ``"/$defs/"`` in the pointer.
  :class:`keywords.Position` is the declaration, :data:`bundle.DESCENDS` is the table, and
  ``nodes_at`` already yields the answer.

So nothing below re-derives a reading the compiler has. Where this module needs a fact
about a node, it asks the module that declares it.

THE THREE GROUPS
----------------

A position is in scope when its ``allOf`` carries exactly one bare ``$ref`` conjunct. It
is grouped by what its own text states ONCE :data:`codegen.catalogue.ANNOTATIONS` is
dropped -- §3a's admission test, *in the key if and only if some instance turns on it*.

``is_the_reference``
    The node's only assertion is that single ``$ref``. In draft-07 a keyword stated
    beside a ``$ref`` is IGNORED, so an author with a sentence to write about a reference
    has one idiom available::

        {"allOf": [{"$ref": ".../core/canonical-account-ref.json"}],
         "description": "Execution account."}

    That admits exactly what the target admits. By §3a's own test it is a §5 ``$ref`` row
    and declares no class.

``narrows``
    The node composes the ``$ref`` and states ``required`` -- it selects among the
    target's branches and declares no member of its own. The type is the target's; which
    branch is a rule on it.

``adds``
    The node composes the ``$ref`` and declares a member the target does not. **This is
    the document's own meaning and the compiler is right to transcribe it** (§5: the
    compiler transcribes a document; it never decides whether the document is
    satisfiable). These crossings are real, and they go to the owner as upstream schema
    candidates rather than being collapsed here.

**AND THE POSITION KIND IS REPORTED BESIDE THE GROUP, because §3a's rule-position clause
does not reach the case that cost the most.** §3a: *"a node inside an ``if``, ``then``,
``else`` or ``not`` is not a stating position of any layer."* Measured against
:data:`bundle.DESCENDS`, those four keywords are exactly ``Position.RULE`` -- and
``anyOf`` is ``Position.BRANCH``, so the clause does not cover a combinator branch at
all. ``media-buy/buy-products-request.json#/anyOf/1/properties/account`` is
``{"required": ["brand", "operator"]}`` under a root ``anyOf``: it declares nothing and
only restricts a member ``#/properties/account`` already references, yet it is a BRANCH
and a class is minted for it. A payload is validated against the whole ``anyOf`` and
never against one branch, so that class admits a set no wire position is checked against.

IT READS AND IT DOES NOT RUN
----------------------------

``survey/format_shapes.py``'s contract: the bundle is the input, the groups are a
grouping of it, and nothing is emitted, compiled or validated to produce the table.
**AND THERE IS NO VERDICT** -- the groups are reported and the decision is read in
``docs/plan/architecture.md`` §3a. An instrument that guesses a verdict is one its reader
learns to discount, which is the lesson ``format_shapes`` records paying for twice.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any

#: What a composing node may state without declaring a member of its own: ``required``
#: selects among the target's branches, and ``allOf`` is the composition itself.
_SELECTS = frozenset({"allOf", "required"})


def _target(ref: object) -> str | None:
    """The bundle-relative document a ``$ref`` names, or ``None`` if it names a node."""
    if not isinstance(ref, str):
        return None
    tail = ref.rsplit("/schemas/", 1)[-1]
    return tail.split("/", 1)[-1] if "/" in tail else tail


def compositions(bundle_dir: Path) -> list[dict[str, Any]]:
    """Every stating position whose ``allOf`` carries one bare ``$ref``, with its group.

    The document screen is :func:`catalogue.stating` and the walk is
    :func:`bundle.nodes_at`; neither reading is restated here.
    """
    from codegen import bundle, catalogue

    annotations = frozenset(catalogue.ANNOTATIONS)
    found: list[dict[str, Any]] = []
    for document in catalogue.stating(bundle_dir):
        node = bundle.read(bundle_dir, document)
        for pointer, held, position in bundle.nodes_at(node):
            row = _one(document, held, pointer, position, annotations)
            if row is not None:
                found.append(row)
    return found


def _one(
    document: str,
    node: dict[str, Any],
    pointer: str,
    position: Any,
    annotations: frozenset[str],
) -> dict[str, Any] | None:
    """Classify ``node`` if it composes exactly one bare ``$ref``."""
    conjuncts = node.get("allOf")
    if not isinstance(conjuncts, list):
        return None
    refs = [
        _target(c["$ref"])
        for c in conjuncts
        if isinstance(c, dict) and set(c) == {"$ref"} and _target(c["$ref"])
    ]
    if len(refs) != 1:
        return None

    #: What the position states about an instance over and above the reference: its own
    #: keywords and every conjunct that is not the reference, annotations dropped.
    stated = {k for k in node if k not in annotations} - {"allOf"}
    for conjunct in conjuncts:
        if isinstance(conjunct, dict) and set(conjunct) != {"$ref"}:
            stated |= {k for k in conjunct if k not in annotations}

    if not stated:
        group = "is_the_reference"
    elif stated <= _SELECTS:
        group = "narrows"
    else:
        group = "adds"
    return {
        "document": document,
        #: **SPELLED AS ``SchemaRef`` SPELLS IT**, which is a ``#`` and then
        #: :func:`bundle.nodes_at`'s pointer -- the root is ``#`` and a property is
        #: ``#/properties/x``.  ``nodes_at`` yields ``""`` for the root and no leading
        #: ``#`` for anything else, so a row keyed on its pointer raw joins the emitted
        #: tree on the ROOTS ALONE: measured, 18 of 73 matched and every PROP position
        #: silently missed, which read as "the compiler already handles these".
        "pointer": f"#{pointer}",
        "position": str(position),
        "target": refs[0],
        "states": tuple(sorted(stated)),
        "group": group,
        "annotated": bool(node.keys() & {"description", "title"}),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True, help="the bundle directory")
    parser.add_argument("--group", help="print every position of one group")
    parser.add_argument("--json", type=Path, help="write the census here as JSON too")
    args = parser.parse_args(argv)

    found = compositions(args.bundle)
    by_group: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in found:
        by_group[row["group"]].append(row)

    documents = {r["document"] for r in found}
    print(
        f"{len(found)} positions compose exactly one $ref, over {len(documents)} of the "
        f"compiler's stating documents\n"
    )
    for group in ("is_the_reference", "narrows", "adds"):
        rows = by_group.get(group, [])
        print(
            f"{group}  —  {len(rows)} positions over "
            f"{len({r['document'] for r in rows})} documents"
        )
        if group == "is_the_reference":
            print(
                "    of those, carrying a description or title: "
                f"{sum(1 for r in rows if r['annotated'])}"
            )
        for states, count in collections.Counter(r["states"] for r in rows).most_common(6):
            print(f"    {count:5d}  states {list(states) or '(the reference alone)'}")
        for kind, count in collections.Counter(r["position"] for r in rows).most_common():
            print(f"          {count:5d}  at Position.{kind}")
        print()

    if args.group:
        print(f"every position of {args.group}:")
        for row in sorted(
            by_group.get(args.group, []), key=lambda r: (r["document"], r["pointer"])
        ):
            print(f"    {row['document']}{row['pointer']}  [{row['position']}]")
            print(f"        -> {row['target']}   states {list(row['states'])}")

    if args.json:
        args.json.write_text(json.dumps(found, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
