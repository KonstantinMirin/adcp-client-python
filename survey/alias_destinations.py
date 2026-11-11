"""The upstream spellings that RESOLVE, and the emitted class each one reaches.

**WHAT THIS ANSWERS, and `docs/migration-from-upstream.md` had no section for it.**  That
guide documents six ways an upstream name can FAIL -- machinery we do not ship, a name that
raises on upstream's own wheel, a name that is not a type, a name with no schema subject, a
name meaning something else, and the instrument's undecided seven.  It had nothing at all
for the much larger set that WORKS: an upstream word the alias layer binds, resolving onto a
class this compiler emitted from a document.  A reader learned about those names only by
their absence from the six failure sections.

**THIS IS NOT A DEPRECATION NOTICE AND MUST NOT READ AS ONE.**  The owner's ruling: the
aliases work and will keep working.  An alias is a NAME and never a second type, so
``isinstance`` holds across every spelling of one subject.  What the section states is a
PRECEDENCE between two true spellings, and the reason: the alias records upstream's 9.6.1
word, while the emitted path is a function of the document.  A bundle bump moves the emitted
name with the document and can retire an upstream word entirely, so the emitted path is the
future-proof spelling -- and an adopter who changes nothing keeps working.

**DERIVED AND NEVER LISTED.**  A thousand rows cannot be maintained by hand and a
hand-written table is stale on the next bundle, so every row and every figure here is read
off the compiler's own record and the alias layers' own tables.  A spelling upstream adds or
drops moves through this with nothing edited.

**IT WRITES NO ALIAS, WHICH IS WHY IT IS NOT A SECOND PAIR WRITER.**
``survey/mechanical_aliases.py``'s ``write_pairs`` exists because reading 10 grades an alias
and its migration entry as one unit, so a derivation that MINTS aliases must write both
halves or neither.  This derivation mints nothing: every word it documents is already bound
and already committed, in ``compat.py``, ``_adapter.py`` or ``_restored.py``.  It is the
second half of pairs whose first half landed, so it writes the guide alone.

**FOUR TABLES, IN THE PRECEDENCE ORDER ``adcp.types.__getattr__`` STATES** -- and the order
is that function's and not this file's, which is why :func:`answered_by` walks it rather than
assuming a winner:

===================================  =====  ===========================================
table                                names  what it is
===================================  =====  ===========================================
``compat.__all__``                     988  the alias table -- every relocated spelling
``compat.__adcp_flat_only__``           79  a word our own domain module already carries
``_adapter.__all__``                   127  upstream's own module-scope flat imports
``_restored.__all__``                  223  what upstream's restored files declare
===================================  =====  ===========================================

The first three figures and the fourth are the ones ``adcp-client-python-b2pm`` measured;
the union is smaller than their sum because a word may stand in two tables, and the brief's
arithmetic of 1,338 left ``__adcp_flat_only__`` out.  Both figures are reported.

**TWO READINGS OF THE COMPILER'S RECORD, AND THE SECOND IS NARROW ON PURPOSE.**  A class
the walk emitted carries its own ``__adcp_schema__`` -- the ``SchemaRef`` ``codegen/emit.py``
writes, naming the document and the pointer the declaration came from -- and that is the
first reading.  A generated ``StrEnum`` cannot carry one as a class attribute without the
value becoming a member, so the emitter puts it on the MODULE; the second reading takes a
module's record only where that module declares exactly ONE name and its pointer is the
document root, which is what a catalogue enum's own module is.  Anything looser would hand a
nested declaration its document's ROOT pointer and the row would name a node the class did
not come from.

**AND THE RECORD MUST BE THE CLASS'S OWN, which is the trap this instrument was built
around.**  ``adcp.types.canonical_creative.CreateMediaBuyResponse1`` is upstream's
hand-written SUBCLASS of our emitted ``CreateMediaBuySuccess``: it INHERITS
``__adcp_schema__``, so ``getattr`` finds a record, the word looks like it reaches an emitted
class, and it does not -- it reaches a different object, and the identity claim a row makes
would be false.  Measured: 32 of the 1,391 words are exactly that.  So the first reading asks
``vars(cls)`` and never ``getattr``, and those 32 are accounted for by name rather than
written as rows.

**THE PATH IS THE DOMAIN SURFACE AND NOTHING ELSE.**  ``adcp.types._surface`` is the
compiler's own per-domain export record -- one module per domain, 23 of them, each
re-exported by the public ``adcp.types.<domain>`` byte for byte
(``tests_emit/test_the_public_domain_path.py``).  A path is admissible only from that set, so
``adcp.types.projections`` and ``adcp.types.canonical_creative`` -- restored machinery of
upstream's that happens to re-export some of our classes -- cannot stand in for a document's
own domain.  Measured with the surface read that way: every row has exactly ONE domain path
and every one of them is in the domain the row's own document derives
(``codegen.emit.domain``), so no row picks between two paths.

**THE BLIND SPOT THIS CLOSES.**  ``survey/adapter_surface.py``'s census of what upstream's
machinery imports cannot see ``adcp/__init__.py``'s ``_LAZY`` map -- the top-level
``from adcp import <Name>`` surface -- and so under-measures real demand.  :func:`lazy_demand`
reads those names too and reports them split three ways: already in one of the four tables,
resolving at ``adcp.types`` through the emitted surface without an alias, or raising there
because it is §1's machinery.

**AND THE PRESENCE-DISPATCHED NODES GET DIFFERENT GUIDANCE, which is the protocol's and not
this package's.**  AdCP 3.2-3.3 states an XOR at eight nodes -- ``required`` plus ``not`` per
branch -- and our classes reproduce it: the base dispatches on the payload's key set, so a
caller hands over the payload and the model selects the branch, and a payload with both keys
or neither is refused with the document's own sentence.  Where an upstream spelling reaches
one of those bases, the future-proof form is not merely the emitted path: it is to stop
selecting a class at all.  :data:`PRESENCE_XOR_NODES` is taken from
``adcp-client-python-j0fr``'s census rather than re-derived here, and
:func:`presence_classes` reports any node of the tree that dispatches the same way and is not
on it, so a set that has grown is visible instead of absorbed.

Run::

    PYTHONPATH=.:src ./.venv/bin/python survey/alias_destinations.py --report
    PYTHONPATH=.:src ./.venv/bin/python survey/alias_destinations.py --write
"""

from __future__ import annotations

import argparse
import collections
import importlib
import json
import pkgutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

GUIDE = ROOT / "docs" / "migration-from-upstream.md"

#: The heading this script owns in the guide, and the markers it writes between.  Rewritten
#: whole on every run, so the generated half can never drift from the alias layers.
SECTION = (
    "## §12. The spellings that RESOLVE: "
    "the alias is upstream's word, the emitted path is the document's"
)
BEGIN = "<!-- GENERATED by survey/alias_destinations.py -- do not edit between the markers -->"

#: What a row's last column adds where the row's target dispatches on the payload's key set.
#:
#: **PAYLOAD** is the owner's guidance for those rows and not a severity: the emitted path
#: resolves there exactly as everywhere else, and the mark says the better edit is to stop
#: naming a class rather than to rename one.
MARKS = {"base": " · **PAYLOAD**", "child": " · **BRANCH**", "": ""}
END = "<!-- END GENERATED -->"

#: The eight nodes where AdCP 3.2-3.3 states an XOR and our base dispatches on the key set.
#:
#: **TAKEN FROM ``adcp-client-python-j0fr``'s CENSUS AND NOT RE-DERIVED**, which is the
#: owner's instruction: that row measured ``parse.presence_clause`` over the bundle -- 308
#: presence-only union nodes, 12 of them ``oneOf``, 11 with a forbid half, 8 expressible as a
#: base plus children -- and these are its eight.  Re-deriving the set here would be a second
#: derivation of one number, which is how a document comes to disagree with the row it cites.
#: :func:`presence_classes` reports every node of the tree that dispatches this way and is NOT
#: here, so growth since that census is visible rather than silently folded in.
#: Why a word in one of the four tables is not a row, and the section whose subject it is.
#:
#: **EVERY ONE OF THESE RESOLVES.**  A withheld word is not a failure this derivation found:
#: it is a word whose destination is not a class compiled from a document, so the triple a
#: row states -- word, emitted class, node -- has no third element to state.  The sections
#: named here are where its subject already lives, so this one does not answer it twice.
WITHHELD_REASONS: dict[str, str] = {
    "declared by a restored module of upstream's, no document": (
        "upstream's own hand-written declaration, served from the file restored at "
        "upstream's own path. §1's subject: no document states it, so there is no emitted "
        "class and no node"
    ),
    "a union or constrained-scalar spelling, not a class": (
        "an `Annotated` constrained scalar or a union over branches — a type expression and "
        "not a class, so it has no `adcp.types.<domain>.<Name>` of its own. §3's subject"
    ),
    "a hand-written subclass of an emitted class": (
        "upstream's `canonical_creative` and `projections` layers, which SUBCLASS a class of "
        "ours. §5's subject — the word reaches their subclass and not our emitted class, "
        "which is exactly the substitution a row here must not claim"
    ),
    "a constant or a function, no document": (
        "a `frozenset`, a tuple or a helper upstream's restored files declare — "
        "`MEDIA_BUY_LEGACY_STATUS_VALUES` is the measured case. §1's subject"
    ),
    "reaches no adcp.types.<domain> export": (
        "the target resolves but no domain module exports it. §4's own remedy applies and it "
        "is not this section's: an EXPORT or a NAME, never a split"
    ),
}

PRESENCE_XOR_NODES = (
    "core/creative-asset.json#",
    "core/creative-manifest.json#",
    "creative/list-creatives-response.json#/properties/creatives/items",
    "core/catchment.json#",
    "core/product-filters.json#/properties/geo_proximity/items",
    "core/targeting.json#/properties/geo_proximity/items",
    "core/frequency-cap-impression-constraints.json#",
    "core/frequency-cap-interval-constraints.json#",
)


def domains() -> list[str]:
    """The 23 domains, off the compiler's own export record.

    ``adcp.types._surface`` is what ``codegen/emit.py``'s ``SURFACE`` writes: one aggregator
    per domain plus the cross-domain ``_flat``.  The domain list is therefore the modules of
    that package that are not private, and there is no table of domains anywhere -- a new
    document appears in its domain with nothing edited.
    """
    surface = importlib.import_module("adcp.types._surface")
    return sorted(
        found.name
        for found in pkgutil.iter_modules(surface.__path__)
        if not found.name.startswith("_")
    )


def domain_surface() -> dict[int, list[str]]:
    """``id(object)`` -> every ``adcp.types.<domain>.<Word>`` path that exports it.

    **KEYED ON THE OBJECT AND NEVER ON A NAME**, which is what makes a row's claim an
    identity claim: a path is in this map because the object AT it is the object asked about,
    so "the word and the path are the same object" is how the row was derived and not
    something asserted about it afterwards.
    """
    out: dict[int, list[str]] = collections.defaultdict(list)
    for domain in domains():
        module = importlib.import_module(f"adcp.types.{domain}")
        for word in module.__all__:
            out[id(getattr(module, word))].append(f"adcp.types.{domain}.{word}")
    return out


def tables() -> dict[str, set[str]]:
    """The four alias tables, by the name a reader of the precedence order sees."""
    compat = importlib.import_module("adcp.types.compat")
    adapter = importlib.import_module("adcp.types._adapter")
    restored = importlib.import_module("adcp.types._restored")
    return {
        "compat": set(compat.__all__),
        "flat_only": set(compat.__adcp_flat_only__),
        "_adapter": set(adapter.__all__),
        "_restored": set(restored.__all__),
    }


def answered_by(word: str, obj: object) -> str:
    """Which layer ``adcp.types.<word>`` actually came from, walking that function's order.

    **THE ORDER IS ``adcp.types.__getattr__``'s AND NOT THIS FILE'S.**  Upstream's own
    statement is asked FIRST -- ``_restored.STATED``, because upstream's flat ``Format`` is
    their hand-written ``canonical_creative.Format`` and not ``core/format.json``'s root --
    and precedence decides only the words upstream states nothing about.  A reader who wants
    to know which table served a word cannot get it from membership: a word stands in two
    tables often enough, and the answer is whichever one the lookup reached.

    Each step confirms by IDENTITY before claiming the layer, so a word two layers hold is
    attributed to the one holding the object the facade actually returned.
    """
    compat = importlib.import_module("adcp.types.compat")
    adapter = importlib.import_module("adcp.types._adapter")
    restored = importlib.import_module("adcp.types._restored")
    if word in restored.STATED and getattr(restored, word, None) is obj:
        return "restored.STATED"
    if getattr(compat, word, None) is obj:
        return "compat"
    where = compat.__adcp_flat_only__.get(word)
    if where is not None and getattr(importlib.import_module(where), word, None) is obj:
        return "flat_only"
    if getattr(adapter, word, None) is obj:
        return "_adapter"
    if getattr(restored, word, None) is obj:
        return "_restored"
    flat = importlib.import_module("adcp.types._surface._flat")
    if getattr(flat, word, None) is obj:
        return "_flat"
    return "unattributed"


def record_of(obj: object) -> tuple[object | None, str]:
    """The ``SchemaRef`` the compiler wrote for this object, and which reading found it.

    Two readings, and the second is narrow for the reason this module's docstring gives.
    ``vars(cls)`` and never ``getattr``: an inherited record belongs to the PARENT, and a
    subclass carrying one is not the class the walk emitted.
    """
    if isinstance(obj, type):
        own = vars(obj).get("__adcp_schema__")
        if own is not None:
            return own, "class"
    module = sys.modules.get(getattr(obj, "__module__", "") or "")
    if module is None or not module.__name__.startswith("adcp.types._schemas."):
        return None, ""
    record = getattr(module, "__adcp_schema__", None)
    declared = tuple(getattr(module, "__all__", ()) or ())
    if record is not None and record.pointer == "#" and len(declared) == 1:
        return record, "module"
    return None, ""


def presence_classes() -> dict[str, object]:
    """The presence-dispatching classes on the domain surface, split by the j0fr census.

    ``_BRANCH_PRESENCE`` is the carrier ``adcp.types._base`` gives a base whose branches are
    selected by the payload's KEY SET rather than by a tagging property's ``const``, and it
    is a ``ClassVar`` -- so the children inherit it and membership alone does not say which
    is a ``ClassVar`` -- so the children inherit it and membership alone does not say which
    class is the base.  **A BASE IS A CLASS WHOSE SUBCLASSES INCLUDE EVERY BRANCH IT
    NAMES**, which is the reading that separates the three cases: a branch class's own
    subclass list is empty or holds a hand-written extension of upstream's, and neither
    contains the sibling branch names.  Both looser readings were measured: "has any
    subclass" counted four branch classes as bases of their own nodes, and an EQUALITY on
    the two name sets lost three real bases, whose subclasses include the branches AND a
    hand-written subclass of upstream's beside them.

    Returns the bases at :data:`PRESENCE_XOR_NODES`, their children, and -- reported rather
    than absorbed -- every other node of the tree dispatching the same way.
    """
    bases: dict[str, type] = {}
    elsewhere: set[str] = set()
    for domain in domains():
        module = importlib.import_module(f"adcp.types.{domain}")
        for word in module.__all__:
            obj = getattr(module, word)
            if not isinstance(obj, type) or not getattr(obj, "_BRANCH_PRESENCE", ()):
                continue
            record = vars(obj).get("__adcp_schema__")
            branches = {name for name, _ in obj._BRANCH_PRESENCE}
            if record is None or not branches <= {kid.__name__ for kid in obj.__subclasses__()}:
                continue
            node = record.document + record.pointer
            if node in PRESENCE_XOR_NODES:
                bases[node] = obj
            else:
                elsewhere.add(node)
    children = {child for base in bases.values() for child in base.__subclasses__()}
    return {"bases": bases, "children": children, "dispatching_elsewhere": sorted(elsewhere)}


def lazy_demand(known: set[str]) -> dict[str, list[str]]:
    """``adcp/__init__.py``'s ``_LAZY`` names, split three ways.

    **THE BLIND SPOT, READ RATHER THAN EXCLUDED.**  ``survey/adapter_surface.py``'s census
    ranges over what upstream's kept machinery imports and cannot see this map, so it
    under-measures the top-level ``from adcp import <Name>`` demand.  Every name here is
    asked of ``adcp.types`` and placed: in one of the four tables already, resolving without
    an alias because our own walk emitted the same word, or raising -- which is §1's
    machinery and not a spelling this section owes anything.
    """
    adcp = importlib.import_module("adcp")
    types_module = importlib.import_module("adcp.types")
    out: dict[str, list[str]] = {"in_a_table": [], "resolves_unaliased": [], "raises": []}
    for name in sorted(adcp._LAZY):
        if name in known:
            out["in_a_table"].append(name)
            continue
        try:
            getattr(types_module, name)
        except AttributeError:
            out["raises"].append(name)
        else:
            out["resolves_unaliased"].append(name)
    return out


def decide() -> dict[str, object]:
    """One verdict per upstream word: a row, or an accounted-for reason there is none."""
    from codegen import emit

    surface = domain_surface()
    table = tables()
    types_module = importlib.import_module("adcp.types")
    presence = presence_classes()
    bases = {id(base): node for node, base in presence["bases"].items()}  # type: ignore[union-attr]
    children = {id(child) for child in presence["children"]}  # type: ignore[union-attr]

    words: dict[str, str] = {}
    for layer in ("compat", "flat_only", "_adapter", "_restored"):
        for word in sorted(table[layer]):
            words.setdefault(word, layer)

    rows: list[dict[str, str]] = []
    withheld: dict[str, list[str]] = collections.defaultdict(list)
    for word in sorted(words):
        obj = getattr(types_module, word)
        record, reading = record_of(obj)
        if record is None:
            if isinstance(obj, type) and getattr(obj, "__adcp_schema__", None) is not None:
                withheld["a hand-written subclass of an emitted class"].append(word)
            elif getattr(obj, "__module__", "") in ("typing", "types"):
                withheld["a union or constrained-scalar spelling, not a class"].append(word)
            elif (getattr(obj, "__module__", "") or "").startswith("adcp.types."):
                withheld["declared by a restored module of upstream's, no document"].append(word)
            else:
                withheld["a constant or a function, no document"].append(word)
            continue
        paths = surface.get(id(obj))
        if not paths:
            withheld["reaches no adcp.types.<domain> export"].append(word)
            continue
        node = record.document + record.pointer
        rows.append(
            {
                "word": word,
                "path": sorted(paths)[0],
                "paths": len(paths),
                "name": sorted(paths)[0].rsplit(".", 1)[1],
                "node": node,
                "reading": reading,
                "domain": emit.domain(record.document),
                "layer": answered_by(word, obj),
                "presence": (
                    "base" if id(obj) in bases else "child" if id(obj) in children else ""
                ),
            }
        )
    return {
        "rows": rows,
        "withheld": dict(withheld),
        "tables": {layer: len(names) for layer, names in table.items()},
        "union": len(words),
        "domains": len(domains()),
        "lazy": lazy_demand(set(words)),
        "presence_nodes": sorted(presence["bases"]),  # type: ignore[arg-type]
        "presence_children": sorted(child.__name__ for child in presence["children"]),  # type: ignore[union-attr]
        "dispatching_elsewhere": presence["dispatching_elsewhere"],
    }


def guide_section(report: dict[str, object]) -> str:
    """The guide's §12, whole, derived from :func:`decide`'s verdicts."""
    rows: list[dict[str, str]] = report["rows"]  # type: ignore[assignment]
    withheld: dict[str, list[str]] = report["withheld"]  # type: ignore[assignment]
    lazy: dict[str, list[str]] = report["lazy"]  # type: ignore[assignment]
    counted = {layer: report["tables"][layer] for layer in report["tables"]}  # type: ignore[index]
    by_layer = collections.Counter(row["layer"] for row in rows)
    at_base = [row for row in rows if row["presence"] == "base"]
    at_child = [row for row in rows if row["presence"] == "child"]
    in_lazy = sum(1 for row in rows if row["word"] in lazy["in_a_table"])
    brief_sum = counted["compat"] + counted["_adapter"] + counted["_restored"]
    one_path = sum(1 for row in rows if row["paths"] == 1)
    branch_clause = (
        "no row reaches a branch class directly"
        if not at_child
        else f"{len(at_child)} reach a branch class directly and carry **BRANCH**"
    )
    layer_counts = ", ".join(
        f"**{layer}** {count:,}"
        for layer, count in sorted(by_layer.items(), key=lambda pair: -pair[1])
    )
    own_domain = sum(
        1 for row in rows if row["path"].startswith(f"adcp.types.{row['domain']}.")
    )

    head = f"""{SECTION}

**NOTHING IN THIS SECTION IS GOING AWAY, and an application that changes none of its imports
goes on working.** The six sections above are about names that FAIL. This one is about the
**{len(rows):,} that WORK**: an upstream spelling the alias layer binds, resolving onto a
class this compiler emitted from a bundle document. Until now they were documented only by
their absence from those six, and the owner's ruling is that their absence said the wrong
thing about them.

### Construct from the payload and let the model choose the branch

**A CALLER SHOULD NEVER NAME A BRANCH CLASS, and this is the AdCP data model rather than a
feature of this package.** At {len(PRESENCE_XOR_NODES)} nodes the bundle states an XOR — a
`required` clause per branch with a `not` forbidding the other's key — so a creative is
addressed one way or the other and never both.
`creative/list-creatives-response.json#/properties/creatives/items` is the case to read: two
branches titled *"Listed creative (named-format reference)"* and *"Listed creative (canonical
format kind)"*, selected by whether `format_id` or `format_kind` is present. So hand the
payload to the base and let it dispatch:

```python
from adcp.types.creative import ListCreativesResponseCreativesItem

ListCreativesResponseCreativesItem.model_validate({{**base, "format_id": ref}})
# -> ListedCreativeNamedFormatReference
ListCreativesResponseCreativesItem.model_validate({{**base, "format_kind": "image"}})
# -> ListedCreativeCanonicalFormatKind
ListCreativesResponseCreativesItem.model_validate(
    {{**base, "format_id": ref, "format_kind": "image"}}
)
# -> refused: "0 of these clauses hold, the document admits exactly one"
ListCreativesResponseCreativesItem.model_validate(base)
# -> refused, the same sentence
```

The XOR is enforced structurally and the caller does not choose. **This holds for anyone
implementing AdCP 3.2–3.3 in any language** — our classes reproduce the document's clause,
they do not invent it — so the guidance is not "use our helper", it is *a creative is
addressed one way or the other, pass what you have, and the model decides*.

**AND WHERE AN UPSTREAM SPELLING REACHES ONE OF THOSE BASES, THAT IS THE FUTURE-PROOF FORM
AND NOT MERELY THE EMITTED PATH.** Upstream's word at such a node names a class that carried
both addressing forms as optional fields, and the edit worth making there is not a rename: it
is to stop selecting a class at all and hand the payload over. **{len(at_base)} rows below
reach one of the {len(PRESENCE_XOR_NODES)} bases** and carry **PAYLOAD** in their last
column — {", ".join(f"`{row['word']}`" for row in at_base)} — and
{branch_clause}.
For every other row the emitted-path rule below is the whole of it. The
{len(PRESENCE_XOR_NODES)} nodes are `adcp-client-python-j0fr`'s census, taken from it rather
than re-derived here.

### The rule, stated once rather than per row

**BOTH SPELLINGS ARE TRUE AND ONE OF THEM IS A FUNCTION OF THE DOCUMENT.** An alias is a
NAME and never a second type — every statement in `compat.py`, `_adapter.py` and
`_restored.py` is a re-export, so the object reached through upstream's word IS the object
the walk emitted, `isinstance` holds across every spelling of one subject, and
`adcp.types.<word> is adcp.types.<domain>.<Name>` for every row below. What separates the two
columns is whose word each one is:

- **the left column is upstream's word**, recorded from their 9.6.1 wheel. It keeps
  resolving. It is pinned to a release of theirs and to nothing else.
- **the right column is the document's**, derived from the node the declaration was compiled
  from. A bundle bump moves it with the document — and it can retire an upstream word
  entirely, which is the one thing the left column cannot survive.

So the emitted path is what a new line should be written against, and an existing line that
works needs no edit. **This is a precedence between two live spellings and not a
deprecation**: no row below is scheduled for removal, and nothing in this section is a
breaking change. The six sections above keep the breaking changes, which are theirs.

### How the {len(rows):,} rows were derived

Read off the compiler's own record and the alias layers' own tables, never off this file's
text — `survey/alias_destinations.py`, committed, and `--write` rewrites this section whole:

| the table | names | what it is |
|---|---|---|
| `compat.__all__` | {counted["compat"]} | the alias table — every relocated upstream spelling |
| `compat.__adcp_flat_only__` | {counted["flat_only"]} | a word our own domain module carries |
| `_adapter.__all__` | {counted["_adapter"]} | upstream's own module-scope flat imports |
| `_restored.__all__` | {counted["_restored"]} | what upstream's restored files declare |
| **the union** | **{report["union"]:,}** | a word may stand in two tables |

The union is {report["union"]:,} and not {brief_sum:,}, which is the three-table sum
`adcp-client-python-b2pm` measured before `__adcp_flat_only__` was counted. Of those
{report["union"]:,} words, **{len(rows):,} reach a class this compiler emitted**, and each
row states four things: the word an application writes today, the emitted class, that
class's own path, and the node the document states it at. The class is the last segment of
the path, so one column carries both.

A row's target is found by OBJECT and never by name: `adcp.types._surface` is the compiler's
own per-domain export record, {report["domains"]} domains, and a path is admissible only
where the object at it IS the object upstream's word resolves to. {one_path:,} of the
{len(rows):,} rows have exactly one such path, and {own_domain:,} of them are in the domain
their own document derives — so no row picks between two paths and none of them is served by
a module outside the domain surface. Which layer answers is `adcp.types.__getattr__`'s
precedence order and not a membership test: upstream's own statement first
(`_restored.STATED`), then the alias table, then `__adcp_flat_only__`, then `_adapter`, then
`_restored` —
{layer_counts}.

**AND THE TOP-LEVEL DEMAND IS READ AND NOT EXCLUDED, which is a blind spot the adapter
census has.** That census ranges over what upstream's kept machinery imports and cannot see
`adcp/__init__.py`'s `_LAZY` map, so it under-measures the `from adcp import <Name>`
surface. Read here: of its
{len(lazy["in_a_table"]) + len(lazy["resolves_unaliased"]) + len(lazy["raises"]):,} names,
**{len(lazy["in_a_table"]):,} are already in one of the four tables** ({in_lazy:,} of them
are rows below), **{len(lazy["resolves_unaliased"]):,} resolve at `adcp.types` with no alias
at all** because our own walk emitted the same word, and **{len(lazy["raises"]):,} raise
there** — §1's machinery, which no document states and this section owes nothing.

| the word written today | the emitted class, at its own path | the document and pointer | layer |
|---|---|---|---|
"""
    body = "".join(
        "| `{word}` | `{path}` | `{node}` | {layer}{mark} |\n".format(
            mark=MARKS[row["presence"]],
            **row,
        )
        for row in rows
    )
    order = sorted(withheld.items(), key=lambda pair: -len(pair[1]))
    tail = f"""
**WHAT IS NOT A ROW, counted and attributed rather than omitted.**
{report["union"]:,} words stand in the four tables and {len(rows):,} are rows. **The other
{report["union"] - len(rows):,} resolve too** — none of them is a failure this derivation
discovered — but each reaches something other than a class compiled from a document, so the
triple a row states has no third element, and each already has a section of its own above:

""" + "".join(
        f"* **{len(names)}** — {WITHHELD_REASONS.get(reason, reason)}.\n"
        for reason, names in order
    ) + f"""
The subclass set is the one this derivation had to be built around, and it is the reason the
record is read from `vars(cls)` and never with `getattr`: such a class INHERITS
`__adcp_schema__` from the class of ours it extends, so `getattr` finds a record, the word
looks like it reaches an emitted class, and it does not — it reaches a different object.
Measured: {len(withheld.get("a hand-written subclass of an emitted class", []))} rows whose
identity claim would have been false.

**Re-derivable, and every row is executable.**
`survey/alias_destinations.py --report` prints every figure above and each withheld set by
name. `tests_emit/test_the_resolving_spellings.py` parses the table out of this file and, for
every row, imports the word from `adcp.types`, imports the path, and requires the two to be
**the same object by identity** — then re-derives the whole set and requires it to equal what
is written here, so a bundle bump that moves an emitted name reddens rather than quietly
leaving this table behind.

**And {len(report["dispatching_elsewhere"])} further nodes dispatch on a key set the same way
and are not in `j0fr`'s {len(PRESENCE_XOR_NODES)}** —
{", ".join(f"`{node}`" for node in report["dispatching_elsewhere"])}. They are reported here
rather than folded into the count above, because the set named there is that row's
measurement and re-deriving it would be a second derivation of one number.
"""
    return head + body + tail


def write(text: str) -> None:
    """Rewrite the section between the markers, inserting it before the re-derivation note."""
    guide = GUIDE.read_text(encoding="utf-8")
    written = BEGIN + "\n\n" + text + "\n" + END
    if BEGIN in guide:
        head, _, rest = guide.partition(BEGIN)
        _, _, tail = rest.partition(END)
        guide = head + written + tail
    else:
        marker = "\n---\n\n## Re-deriving this document"
        head, _, tail = guide.partition(marker)
        guide = head + "\n---\n\n" + written + "\n" + marker.lstrip("\n") + tail
    GUIDE.write_text(guide, encoding="utf-8")
    print(f"{GUIDE.name}: {SECTION.split('.')[0]} rewritten")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    report = decide()
    rows: list[dict[str, str]] = report["rows"]  # type: ignore[assignment]
    # **EVERY SET IS CLAIMED BEFORE A FIGURE IS READ OFF IT** -- `tests_emit/nodeset.py`'s
    # rule, said here because a survey script cannot import the suite's helpers: "a
    # derivation that selects nothing passes every assertion over it and is
    # indistinguishable from a working check."  Three sets, and each one has been empty
    # during this row's own development: the tables (an import that half-failed), the rows
    # (a record reading that matched nothing), and the presence bases (a carrier renamed).
    for name, members in (
        ("the four alias tables", [n for names in report["tables"].values() for n in [names]]),  # type: ignore[union-attr]
        ("resolving spellings", rows),
        ("presence XOR bases", report["presence_nodes"]),  # type: ignore[arg-type]
        ("_LAZY top-level demand", report["lazy"]["in_a_table"]),  # type: ignore[index]
    ):
        if not members:
            raise SystemExit(
                f"REFUSED: {name}: empty set -- every assertion over it holds vacuously"
            )
    missing = set(PRESENCE_XOR_NODES) - set(report["presence_nodes"])  # type: ignore[arg-type]
    if missing:
        raise SystemExit(
            f"REFUSED: nodes j0fr's census names that do not dispatch on a key set here: "
            f"{sorted(missing)} -- the set moved and the section would state a membership "
            f"nothing holds"
        )
    print(f"four tables                {report['tables']}")
    print(f"union of the four          {report['union']}")
    print(f"ROWS (word -> emitted)     {len(rows)}")
    print(f"  record on the class      {sum(1 for r in rows if r['reading'] == 'class')}")
    print(f"  record on its module     {sum(1 for r in rows if r['reading'] == 'module')}")
    print(f"  at a presence XOR base   {sum(1 for r in rows if r['presence'] == 'base')}")
    print(f"  at a presence branch     {sum(1 for r in rows if r['presence'] == 'child')}")
    for layer, count in sorted(collections.Counter(r["layer"] for r in rows).items()):
        print(f"  answered by {layer:<16} {count}")
    for reason, names in sorted(report["withheld"].items(), key=lambda p: -len(p[1])):  # type: ignore[union-attr]
        print(f"withheld {len(names):>4}             {reason}")
    lazy: dict[str, list[str]] = report["lazy"]  # type: ignore[assignment]
    for key, names in lazy.items():
        print(f"_LAZY {key:<22} {len(names)}")
    found = len(report["presence_nodes"])  # type: ignore[arg-type]
    print(f"presence XOR nodes         {found} of {len(PRESENCE_XOR_NODES)} claimed")
    print(f"dispatching elsewhere      {report['dispatching_elsewhere']}")
    if args.json:
        args.json.write_text(json.dumps(report, indent=1, default=str))
    if args.report:
        for reason, names in sorted(report["withheld"].items()):  # type: ignore[union-attr]
            for name in names:
                print(f"  WITHHELD [{reason}] {name}")
        for name in lazy["raises"]:
            print(f"  LAZY-RAISES {name}")
        for name in lazy["resolves_unaliased"]:
            print(f"  LAZY-UNALIASED {name}")
    if args.write:
        write(guide_section(report))


if __name__ == "__main__":
    main()
