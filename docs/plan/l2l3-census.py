#!/usr/bin/env python3
"""§3a's L2 and L3 census, under the key decided 2026-11-03.

``docs/plan/architecture.md`` §3a, "A LAYER'S KEY CONTAINS EXACTLY WHAT CHANGES THE SET OF
ADMITTED INSTANCES, AND NOTHING ELSE":

* the key holds the property NAMES, ``required``, ``additionalProperties`` and every
  narrowing keyword -- each changes what is admitted;
* it does NOT hold a ``title``, a ``description``, an ``examples``, or property ORDER;
* **references resolve to what they name before keying** -- an unresolved key undercounts,
  measurably so at the array layer;
* a key read off the RENDERED ANNOTATION is not this key.

Three further consequences of "in the key if and only if some instance turns on it", each
of which this file applies and none of which §3a spells:

* a ``definitions``/``$defs`` SECTION is out.  An entry no ``$ref`` names admits nothing,
  and an entry one does name is already in the key at the referring site because
  references resolve.  Keeping it would make two nodes that admit exactly the same set
  differ on a side-car, which is the error the sentence exists to prevent.
* ``required``'s LIST ORDER is out, for the same reason property order is: no payload can
  see it.  ``enum``'s order stays in, because ``codegen/catalogue.py``'s own docstring
  measures the cost of dropping it (``["closed","open"]`` and ``["open","closed"]`` are
  two vocabularies the bundle means to keep apart, and the rendered member ORDER is a
  fact a consumer meets).
* a combinator's BRANCH/CONJ order is out -- ``allOf``, ``anyOf``, ``oneOf`` are sets to
  an instance.

    python docs/plan/l2l3-census.py            the two censuses
    python docs/plan/l2l3-census.py --split    the three-way split per L2 group
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from codegen import bundle, catalogue, keywords  # noqa: E402

BUNDLE = Path("schemas/cache/3.2")

#: The keywords whose subschemas sit at a DEF position: a SECTION, not an admission.
SECTIONS = frozenset(
    k for k, p in bundle.DESCENDS.items() if p is keywords.Position.DEF
)
#: Order-blind subschema lists: a combinator is a SET to an instance.
UNORDERED = bundle.HELD_IN_A_LIST
#: Named subschema bags: ``properties``, ``patternProperties``.
BY_NAME = bundle.HELD_BY_NAME - SECTIONS

CYCLE = "<cycle>"


class Keyer:
    """The decided key, computed over a bundle with references resolved."""

    def __init__(self, bundle_dir: Path) -> None:
        self.dir = bundle_dir
        self.documents = frozenset(bundle.portable(bundle_dir))
        self._read: dict[str, dict] = {}

    def doc(self, name: str) -> dict:
        if name not in self._read:
            self._read[name] = bundle.read(self.dir, name)
        return self._read[name]

    def target(self, document: str, uri: object) -> tuple[str, str] | None:
        """``(document, pointer)`` a ``$ref`` names, or ``None`` where nothing does."""
        if not isinstance(uri, str):
            return None
        head, pointer = bundle.split_ref(uri)
        if head == "":
            return (document, pointer)
        named = bundle.document_for(head, self.documents)
        return None if named is None else (named, pointer)

    def key(self, document: str, node: object, stack: tuple[tuple[str, str], ...] = ()) -> object:
        if isinstance(node, list):
            return ("[]", tuple(self.key(document, v, stack) for v in node))
        if not isinstance(node, dict):
            return json.dumps(node, sort_keys=True)
        out: list[tuple[str, object]] = []
        for word in sorted(node):
            if word in catalogue.ANNOTATIONS or word.startswith("x-") or word in SECTIONS:
                continue
            held = node[word]
            if word == "$ref":
                at = self.target(document, held)
                if at is None:
                    out.append((word, ("unresolved", json.dumps(held))))
                elif at in stack:
                    out.append((word, (CYCLE, len(stack) - stack.index(at))))
                else:
                    reached = bundle.node_at(self.doc(at[0]), at[1])
                    out.append((word, self.key(at[0], reached, stack + (at,))))
            elif word in BY_NAME and isinstance(held, dict):
                out.append(
                    (
                        word,
                        tuple(sorted((k, self.key(document, v, stack)) for k, v in held.items())),
                    )
                )
            elif word in UNORDERED and isinstance(held, list):
                out.append(
                    (word, tuple(sorted(repr(self.key(document, e, stack)) for e in held)))
                )
            elif word in bundle.DESCENDS:
                out.append((word, self.key(document, held, stack)))
            elif word == "required" and isinstance(held, list):
                out.append((word, tuple(sorted(map(str, held)))))
            else:
                out.append((word, json.dumps(held, sort_keys=True)))
        return tuple(out)


class Stated(collections.namedtuple("Stated", "document pointer position key title")):
    """One stating position at a layer, and the decided key it states."""

    @property
    def is_a_root(self) -> bool:
        return self.pointer == ""


def states(keyer: Keyer, layer: str) -> list[Stated]:
    """Every position of the bundle that STATES an object (L2) or an array (L3) type.

    L2 is a node holding ``properties`` with at least one entry -- the population the
    42 row's split was asked of.  L3 is a node holding ``items``, which is what an array
    type IS; it declares no class (an array renders as ``list[X]`` inside an annotation),
    which is why reading 4's ``Decided by`` says this layer is read off the bundle.
    """
    out: list[Stated] = []
    names = bundle.named_nodes(keyer.dir)
    for document in sorted(keyer.documents):
        doc = keyer.doc(document)
        unreferenced = tuple(
            sorted(bundle.section_entries(doc) - names.get(document, frozenset()))
        )
        for pointer, node, position in bundle.nodes_at(doc):
            # **A RULE POSITION MINTS NO TYPE.**  §3's RULE position is where ``if``,
            # ``then``, ``else`` and ``not`` hold their subschemas, and a conditional's
            # subschema compiles to a RULE rather than to a type -- so a node holding
            # ``properties`` there states a constraint on an instance of the ENCLOSING
            # type and declares none of its own.  Measured: 806 of the 3,261 nodes of
            # this bundle that hold a non-empty ``properties`` sit at a RULE, and
            # excluding them reproduces the 42 row's 2,455 exactly.
            if position is keywords.Position.RULE:
                continue
            # A ``definitions`` entry no ``$ref`` names lowers nothing (§5), which is
            # ``catalogue.Stated.reached``'s own reading at L0.
            if any(pointer.startswith(entry) for entry in unreferenced):
                continue
            if layer == "L2":
                held = node.get("properties")
                if not isinstance(held, dict) or not held:
                    continue
            else:
                if not isinstance(node.get("items"), dict):
                    continue
            title = node.get("title")
            out.append(
                Stated(
                    document=document,
                    pointer=pointer,
                    position=position,
                    key=repr(keyer.key(document, node)),
                    title=title if isinstance(title, str) and title.strip() else None,
                )
            )
    return out


def census(positions: list[Stated]) -> dict[str, object]:
    groups: dict[str, list[Stated]] = {}
    for p in positions:
        groups.setdefault(p.key, []).append(p)
    repeated = {k: g for k, g in groups.items() if len(g) > 1}
    cross = {
        k: g for k, g in repeated.items() if len({p.document for p in g}) > 1
    }
    titled = {k: g for k, g in cross.items() if {p.title for p in g} - {None}}
    return {
        "positions": len(positions),
        "identities": len(groups),
        "repeated": len(repeated),
        "repeated positions": sum(len(g) for g in repeated.values()),
        "cross-document": len(cross),
        "cross-document positions": sum(len(g) for g in cross.values()),
        "documents": len({p.document for g in cross.values() for p in g}),
        "titled": len(titled),
        "untitled": len(cross) - len(titled),
        "widest": max((len(g) for g in groups.values()), default=0),
        "_groups": groups,
        "_cross": cross,
    }


def main(argv: list[str]) -> int:
    keyer = Keyer(BUNDLE)
    for layer in ("L2", "L3"):
        c = census(states(keyer, layer))
        print(f"\n=== {layer} ===")
        for name, value in c.items():
            if not name.startswith("_"):
                print(f"  {name:28} {value}")
        if "--split" in argv:
            for key, group in sorted(c["_cross"].items(), key=lambda kv: -len(kv[1])):
                titles = sorted({p.title for p in group if p.title})
                roots = sum(1 for p in group if p.is_a_root)
                print(
                    f"    {len(group):4} positions  "
                    f"{len({p.document for p in group}):3} docs  "
                    f"roots {roots:3}  titles {len(titles):2}  {titles[:3]}"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
