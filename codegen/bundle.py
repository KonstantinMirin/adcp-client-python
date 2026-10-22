"""The schema bundle: which documents it holds, and reading one.

The bundle directory is an argument everywhere (D9), so nothing here knows a
version and no caller can pass one by accident -- there is no default.

``portable`` is the population the metric is stated over: every document the
bundle publishes under its own identity.  ``bundled/`` and ``mcp/`` are
PROJECTIONS of those documents (the same nodes re-cut for one transport), and
the three registry files describe the bundle rather than a message, so neither
is a document to emit.  On the 3.2 bundle that leaves 1,054, which is the
denominator in the plan's metric.
"""

from __future__ import annotations

import json
from collections.abc import Collection, Iterator
from pathlib import Path

from codegen.harness import resolve

#: Top-level directories holding projections of documents published elsewhere.
PROJECTIONS = ("bundled", "mcp")
#: Files describing the bundle, not a message.
REGISTRY = ("index.json", "manifest.json", "manifest.schema.json")


def portable(bundle: Path) -> list[str]:
    """Every document path, bundle-relative, in sorted order (P7)."""
    out = [
        str(p.relative_to(bundle))
        for p in bundle.rglob("*.json")
        if p.relative_to(bundle).parts[0] not in PROJECTIONS
        and str(p.relative_to(bundle)) not in REGISTRY
    ]
    return sorted(out)


def read(bundle: Path, document: str) -> dict:
    doc = json.loads((bundle / document).read_text())
    if not isinstance(doc, dict):
        raise ValueError(f"{document}: document root is {type(doc).__name__}, not an object")
    return doc


# --------------------------------------------------------------------------- #
# the census of node kinds this step's population is selected by
# --------------------------------------------------------------------------- #
# Descend only where a subschema can legally appear.  The same reason
# ``harness.formats_used`` does: ``examples``, ``default``, ``const`` and ``enum``
# hold INSTANCE data, so a key named ``$ref`` or ``allOf`` beneath one of them is
# a data field whose name collides, and a blanket walk reports a composition this
# document does not have.
_DESCEND_MAP = ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas")
_DESCEND_ONE = (
    "items",
    "additionalProperties",
    "contains",
    "not",
    "if",
    "then",
    "else",
    "propertyNames",
    "additionalItems",
    "unevaluatedProperties",
    "unevaluatedItems",
)
_DESCEND_LIST = ("oneOf", "anyOf", "allOf", "prefixItems")

COMPOSITION = ("allOf", "oneOf", "anyOf")
CONDITIONAL = ("if", "then", "else", "not")
DEFINITIONS = ("definitions", "$defs")


def nodes(node: object, pointer: str = "") -> Iterator[tuple[str, dict]]:
    """Every ``(JSON Pointer, subschema)`` at a SCHEMA POSITION in the document.

    The one walk.  ``schema_keywords`` and ``references`` are both read off it, so
    the two censuses cannot come to disagree about what a schema position is --
    which is the same reason ``harness`` declares its descent tables beside both
    of its walks.
    """
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from nodes(v, f"{pointer}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield pointer, node
    for k, v in node.items():
        if k in _DESCEND_MAP and isinstance(v, dict):
            for kk, vv in v.items():
                yield from nodes(vv, f"{pointer}/{k}/{kk.replace('~', '~0').replace('/', '~1')}")
        elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
            yield from nodes(v, f"{pointer}/{k}")
        elif k in _DESCEND_LIST and isinstance(v, list):
            yield from nodes(v, f"{pointer}/{k}")


def schema_keywords(node: object) -> set[str]:
    """Every key appearing at a SCHEMA POSITION anywhere in the document."""
    return {k for _, n in nodes(node) for k in n}


def references(node: object) -> list[tuple[str, str]]:
    """Every ``(pointer, $ref)`` at a schema position, in document order."""
    return [(p, n["$ref"]) for p, n in nodes(node) if isinstance(n.get("$ref"), str)]


def document_for(uri: str, documents: Collection[str]) -> str | None:
    """The bundle document an absolute ``$ref`` URI names, or ``None``.

    Derived from the bundle's own file set rather than from the URI's spelling: the
    longest trailing run of path segments that IS a document in this bundle.  That
    is what keeps a version out of ``codegen/`` (D9).  Every reference in the 3.2
    bundle is spelled ``.../schemas/3.2.4/<path>``, and a rule that stripped "the
    version segment" would be a version literal in disguise -- it would also be
    wrong for a bundle that publishes under a different base.

    MEASURED on the 3.2 bundle: of 968 distinct targets, 738 carry no fragment and
    every one of them resolves, with exactly one matching suffix each -- so the
    "longest" is not covering an ambiguity, there is none to cover.  The remaining
    230 carry a fragment and are ``None`` here: a fragment names a NODE inside a
    document, which needs a name of its own, so it is a later step's row and this
    step refuses it.
    """
    if "#" in uri:
        return None
    parts = uri.split("://", 1)[-1].split("/")
    found = [s for i in range(len(parts)) if (s := "/".join(parts[i:])) in documents]
    return max(found, key=len) if found else None


def resolved(bundle_dir: Path, document: str) -> dict:
    """``document``, with every ``$ref`` in it inlined from this bundle.

    THE SELF-CONTAINED FORM, and both consumers need exactly it:

    * ``AdCPBaseModel.strict_validate`` decides acceptance against the document
      the emitter wrote into the package beside the module, which is the one its
      class names on ``__adcp_schema__`` (D4).  The RAW document of a referencing
      class is not decidable there: ``jsonschema`` meets an absolute ``$ref``,
      finds no store, and FETCHES IT OVER THE NETWORK -- measured at 4.4 s per
      validation against a live URL, on a code path ``jsonschema`` deprecates and
      says "will shortly become an error".  Offline it raises instead.  So the
      package carries this.
    * ``check_pair``'s whole input is a document with no reference left in it.

    One function for both, and the class names ONE document, so the schema the
    runtime decides with and the schema the harness grades cannot be two
    different schemas -- there is no second artifact for them to disagree
    through.

    ``harness.resolve`` does the inlining -- the resolution the harness itself
    uses, rather than a second cheaper one, because a cheaper resolution that
    changed a verdict would be a different resolution.  The store is the
    transitive closure of THIS document's references, read off the same ``$ref``
    strings the emitter walks, so a document with none is handed back as read and
    nothing resolves a bundle.  It inlines a fresh copy per path through the graph
    (which is why ``acp-sdkgen/codegen/resolved_cache.py`` exists); over the
    emitted population that is affordable and measured -- 0.84 s for all 43, the
    largest 3,079 bytes -- because an emitted document's targets are leaves or
    aliases: a target that composes refuses and takes its referrer with it.

    KNOWN CEILING, and the point at which ``resolved_cache`` stops being optional:
    this is O(paths through the ref graph), and the bundle holds a 9,109-byte
    document that resolves to 4.8 MB.  Step 8 emits the whole population and will
    meet it; step 2's 43 do not.
    """
    known = set(portable(bundle_dir))
    doc = read(bundle_dir, document)
    store: dict[str, dict] = {}
    queue = [doc]
    while queue:
        for _, uri in references(queue.pop()):
            if uri in store:
                continue
            target = document_for(uri, known)
            if target is None:
                raise ValueError(f"{document}: {uri} names no document of {bundle_dir}")
            store[uri] = read(bundle_dir, target)
            queue.append(store[uri])
    return resolve(doc, store=store) if store else doc


# --------------------------------------------------------------------------- #
# the dispatch table's selectors: which ROW lowers a document's root
# --------------------------------------------------------------------------- #
# One predicate per D2 root row, and together they are a PARTITION of the bundle's
# documents by what their root IS -- so ``emit.ROWS`` is unordered and two rows
# selecting one document is a defect in these predicates rather than a question of
# precedence.  They live beside the population selectors below because a selector
# and the population a step's result is stated over are the same kind of thing, and
# for step 6 they are literally the same predicate: ``is_container_root`` is both the
# row's selector and the list of documents step 6 names.
#
# Disjointness is by construction and is asserted in ``tests/test_emit.py``: a root
# with ``properties`` is an object and a root whose ``type`` is one scalar name is a
# scalar.  A root that is neither -- an array, a propertyless object, an enum, a
# ``oneOf``, an ``allOf`` -- has no row yet and is refused by name, which is steps
# 3 to 6.


def is_object_root(doc: dict) -> bool:
    """D2's object row: a root declaring ``properties``."""
    return "properties" in doc and doc.get("type") in (None, "object")


def is_scalar_root(doc: dict) -> bool:
    """D2's root-scalar row: a root whose ``type`` names one scalar."""
    return doc.get("type") in ("string", "integer", "number", "boolean")


def is_leaf_object(doc: dict) -> bool:
    """Step 1's population: an object root with no reference, composition,
    conditional or definition section anywhere in it."""
    if "properties" not in doc or doc.get("type") not in (None, "object"):
        return False
    kw = schema_keywords(doc)
    return not kw & {"$ref", *COMPOSITION, *CONDITIONAL, *DEFINITIONS}


def references_a_property(doc: dict) -> bool:
    """Step 2's population: every reference in the document is a property's own
    schema or that property's ``items``.

    A reference anywhere else -- an ``allOf`` conjunct, a union branch, a
    ``definitions`` entry -- is a composition, and composition is steps 4-7.  The
    position test is what selects the population; it is not what ENFORCES the
    restriction, because ``lower_object`` descends into ``properties`` and nothing
    else, so a reference elsewhere is refused at its own composition keyword
    before any reference is read.
    """
    rs = references(doc)
    return bool(rs) and all(_is_property_or_items(p) for p, _ in rs)


def _is_property_or_items(pointer: str) -> bool:
    parts = [p for p in pointer.split("/") if p]
    if not parts or parts[0] != "properties":
        return False
    return len(parts) == 2 or (len(parts) == 3 and parts[2] == "items")
