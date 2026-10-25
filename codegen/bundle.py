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

from adcp.types._base import applied_schema

from codegen import compiler
from codegen.harness import resolve
from codegen.lower import rules, union

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
#: The two keywords holding a bag of named subschemas, named ONCE and in the module
#: both halves of the walk can import: ``compiler.check_keywords`` admits them at every
#: node and the selectors below exclude a document declaring one, so a second literal
#: here is a second place for the pair to drift.
DEFINITIONS = compiler.DEFINITION_SECTIONS


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
                yield from nodes(vv, f"{pointer}/{k}/{compiler.escape_key(kk)}")
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


def split_ref(uri: str) -> tuple[str, str]:
    """A ``$ref`` URI as ``(the document it names, the JSON Pointer into it)``.

    THE ONE READING OF THE ``#``, and all three callers need it: ``document_for``
    matches the document half, ``resolved`` keys its store on it, and the emitter's
    reference binder needs both halves because a fragment reference becomes an
    IMPORT and an import needs the module AND the symbol.  Two readings of the same
    delimiter is how a binder and a resolver come to disagree about which document a
    reference names.

    A LOCAL reference (``#/definitions/x``) has an EMPTY document half, which is the
    two cases a caller distinguishes on: a pointer into the referrer, not a document
    this bundle fails to hold.

    A POINTER and not an arbitrary fragment: draft-07 also admits a plain-name
    fragment (``#foo``, resolved against an ``$id``), and this bundle holds none --
    all 154 of its local refs and all 76 of its fragment-bearing absolute refs spell
    a pointer, which starts with ``/`` or is empty.  A plain-name fragment would
    arrive as a pointer naming no node and be refused for naming none, which is the
    right outcome by the wrong reason; the step whose bundle carries one reads
    ``$id``.
    """
    head, _, pointer = uri.partition("#")
    return head, pointer


def document_for(document_uri: str, documents: Collection[str]) -> str | None:
    """The bundle document a ``$ref``'s DOCUMENT HALF names, or ``None``.

    Derived from the bundle's own file set rather than from the URI's spelling: the
    longest trailing run of path segments that IS a document in this bundle.  That
    is what keeps a version out of ``codegen/`` (D9).  Every reference in the 3.2
    bundle is spelled ``.../schemas/3.2.4/<path>``, and a rule that stripped "the
    version segment" would be a version literal in disguise -- it would also be
    wrong for a bundle that publishes under a different base.

    **The DOCUMENT HALF, which the caller takes off the URI with** :func:`split_ref`.
    This function read ``if "#" in uri: return None`` and called a fragment a later
    step's row; this is that row, and the row turns out not to live here. A fragment
    reference needs BOTH halves -- it becomes an import of a symbol the target module
    declares, so the import needs the module AND the symbol -- so the caller splits
    once and uses both, and this reads no ``#`` at all.  Doing the split here as well
    would be a second reading of the delimiter that no live call could reach, since
    every caller arrives pre-split.

    A LOCAL reference (``#/definitions/x``) has an EMPTY document half, and the caller
    branches on that before asking: it names a node of the REFERRER, so no bundle
    document is being named.  ``resolved`` skips one and ``harness.resolve`` resolves
    it against the referrer with no store entry (probed: an empty store inlines
    ``#/definitions/x``).

    MEASURED on the 3.2 bundle: 968 distinct ``$ref`` URIs -- 738 absolute with no
    fragment, 76 absolute carrying one, 154 local.  All 814 absolute ones resolve to
    a document, with exactly one matching suffix each, so the "longest" is not
    covering an ambiguity; there is none to cover.  All 76 fragment pointers name a
    node that exists in the document they resolve to.  (The 230 an earlier revision
    of this docstring called "carrying a fragment" is 76 + 154: it counted the local
    refs in with the absolute ones, which is why it read as 230 unresolvable targets
    rather than as 76 nodes and 154 self-references.)
    """
    parts = document_uri.split("://", 1)[-1].split("/")
    found = [s for i in range(len(parts)) if (s := "/".join(parts[i:])) in documents]
    return max(found, key=len) if found else None


def named_nodes(bundle_dir: Path) -> dict[str, frozenset[str]]:
    """For each document, the pointers of its nodes that a ``$ref`` NAMES.

    A fragment reference resolves to a SYMBOL the target module declares (section 2's
    rule), so that module has to declare one -- and a node that D2 makes an annotation
    rather than a class has no symbol unless something asks for it.  This is what asks.

    **Both kinds of reference ask, and the document they ask of is the one the
    reference RESOLVES AGAINST.**  An absolute fragment reference asks of the document
    its own half names; a LOCAL one (``#/definitions/x``, an empty document half --
    :func:`split_ref`) asks of the REFERRING document, because that is what a pointer
    with no document half means.  The two differ in how the symbol is reached and not
    in whether one is needed: an absolute reference becomes an import, a local one is a
    name already in the module being written.  Keying a local reference against its own
    document is therefore the whole of the difference here, and it is why ``document``
    appears on the left of the assignment below as well as ``target``.

    **A function of the BUNDLE and not of the run's document set**, which is the
    whole reason it is computed here rather than from the ``$ref``\\ s the run's own
    documents happen to carry.  P7 makes the output a function of (bundle, document
    set, this package); a module whose CONTENT varied with which other documents
    were named would satisfy that letter and break its point -- the committed
    ``core/version_envelope.py`` would differ from the one the README's
    one-document command writes, at the same bundle, and the gate's byte compare
    would then be against whichever population last ran.  A local reference satisfies
    that too, for a sharper reason: the document asking and the document asked are the
    same file, so no other document can affect the answer at all.

    Reads every portable document once.  Measured on the 3.2 bundle: 76 pointers
    across 19 documents from 113 ABSOLUTE fragment sites in 34 documents, and 157
    pointers across 45 documents from 405 LOCAL sites -- 402 of those sites naming a
    ``definitions``/``$defs`` entry at a document root, 3 naming one inside the
    bundle's single nested section
    (``brand/get-brand-identity-response.json#/oneOf/0/properties/fonts``) and 0
    naming a document root or a node that is not an entry.  **216 pointers across 54
    documents in all, and not 233**: 10 documents are named by both kinds and 17 of
    their pointers by both, which the set union is what absorbs.
    """
    known = set(portable(bundle_dir))
    out: dict[str, set[str]] = {}
    for document in sorted(known):  # sorted, like ``portable``: P7
        for _, uri in references(read(bundle_dir, document)):
            head, pointer = split_ref(uri)
            if not pointer:
                continue
            if not head:
                out.setdefault(document, set()).add(pointer)
                continue
            target = document_for(head, known)
            if target is not None:
                out.setdefault(target, set()).add(pointer)
    return {d: frozenset(p) for d, p in out.items()}


def constrained_to_object(doc: dict) -> frozenset[str]:
    """The pointers of nodes that state no ``type`` and that the DOCUMENT applies
    ``type: "object"`` to anyway.

    draft-07 applies a root's assertions and its combinator branch's to the SAME
    instance, so ``{"type": "object", "oneOf": [{"properties": {...}}]}`` admits only
    objects and the branch at ``/oneOf/0`` does not have to restate it.  Read in
    ISOLATION that branch admits a non-object, which is what ``compiler.lower_object``
    refused it for -- a fact three lines up in its own document.  10 documents of the
    3.2 bundle were refused for exactly that, and another 34 chained off them through
    a ``$ref``.

    **The rule is ``_base.applied_schema``'s and is not restated here.**  That
    function is what the RUNTIME resolves a class's ``__adcp_schema__`` through, so
    deriving the lowering's answer from it is what makes it impossible for the
    emitter to admit a node whose class would then be narrower than the schema it
    names.  Two spellings of "which hop keeps the instance" is precisely how that
    divergence would arrive, and it would arrive silently.

    A function of the DOCUMENT alone, like every other derived fact here, over
    :func:`nodes` -- the one walk -- so there is no second table of what a schema
    position is either.

    The node's own ``type`` always wins, so this set holds only nodes that declare
    none: a node declaring ``string`` under a root declaring ``object`` states a
    contradiction and stays refused rather than being quietly rewritten.  A
    ``["object", "null"]`` enclosing type admits a null, so it is not a string and
    constrains nothing here.

    Measured on the 3.2 bundle over all 1,054 portable documents: 1,390 nodes declare
    a non-empty ``properties`` without ``type: "object"``; 556 of them, in 151
    documents, are in this set and 834, in 206 documents, are not.
    """
    return frozenset(
        p
        for p, n in nodes(doc)
        if "type" not in n and applied_schema(doc, p).get("type") == "object"
    )


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
        for pointer, uri in references(queue.pop()):
            # **The store is keyed on the DOCUMENT URI and holds the whole
            # document; the resolver follows the fragment itself.**  Keying on the
            # full URI is what this did, and it is why a fragment-bearing reference
            # failed even with its target read in: probed on
            # ``hypothesis_jsonschema``'s resolver, a store holding the target
            # under ``<uri>#/properties/cat`` raises ``_RefResolutionError`` ("does
            # not fetch remote references") while the same target under ``<uri>``
            # inlines the node at the pointer.  So the ``None`` was never the only
            # gate -- the key was the other half.
            #
            # A LOCAL reference is SKIPPED rather than looked up: it names a node of
            # this document, and ``LocalResolver`` is built with ``referrer=doc``,
            # so it resolves one with no store entry at all.  Looking it up instead
            # raised for 93 of the 1,054 portable documents, and 63 of those carry
            # no absolute fragment reference at all -- a document whose only
            # unresolvable reference was a pointer into itself.
            head = split_ref(uri)[0]
            if not head or head in store:
                continue
            target = document_for(head, known)
            if target is None:
                raise ValueError(
                    f"{document}: {uri} at {pointer or '/'} names no document of {bundle_dir}"
                )
            store[head] = read(bundle_dir, target)
            queue.append(store[head])
    # ``references(doc)`` and not ``store``: a document whose only reference is a
    # pointer into ITSELF builds an empty store and still has a ``$ref`` to inline,
    # so the old ``if store`` would hand it back with the reference left in -- which
    # is the one thing this function exists to prevent.  13 documents are in that
    # position (45 carry a local reference, and the other 32 carry an absolute one as
    # well, so their store is not empty).  A document with no reference of its own is
    # handed back as read, and nothing resolves a bundle.
    return resolve(doc, store=store) if references(doc) else doc


# --------------------------------------------------------------------------- #
# the dispatch table's selectors: which ROW lowers a document's root
# --------------------------------------------------------------------------- #
# One predicate per D2 root row, and together they are a PARTITION of the bundle's
# documents by what their root IS -- so ``emit.ROWS`` is unordered and two rows
# selecting one document is a defect in these predicates rather than a question of
# precedence.  They live beside the population selectors below because a selector
# and the population a step's result is stated over are the same kind of thing.
#
# Disjointness is by construction and asserted in ``tests/test_emit.py``, over the
# whole bundle and in both directions.  Each row that lands adds its EXCLUSION to
# the two generic rows here rather than a precedence line to the table: a root
# ``oneOf`` makes the document a union whatever else it declares, and a root
# ``enum`` makes it an enumeration though its ``type`` names a scalar, so the
# clauses below are what keep this a partition.


def declares_its_own_root_kind(doc: dict) -> bool:
    """Does the root declare a kind of its OWN, which one of the specific rows owns?

    A root is exactly ONE kind, and each keyword here decides it whatever else the
    root declares: an ``enum`` at the root makes the document an enumeration though
    its ``type`` names a scalar; an ``allOf`` at the root makes it a composition
    though it declares ``properties`` as well -- a draft-07 root ``allOf`` applies
    to the whole instance, so a row that lowered the properties without the
    conjuncts would drop the bases; and a ``oneOf``/``anyOf`` at the root makes it a
    union whatever else it declares, for the same reason read the other way round.

    Measured, so each clause is known to be load-bearing rather than defensive:
    without the union clause ``is_object_root`` and ``union_root`` both claim 35
    documents and ``is_scalar_root`` and ``union_root`` both claim 1; without the
    ``allOf`` clause the object row collides with step 4's.

    So the two GENERIC rows below are "none of these, and <shape>".  That is what
    makes ``emit.ROWS`` a partition by construction, and it is a fact about the
    SELECTORS rather than a precedence rule in the table: D13 says a collision is a
    selector defect and gets fixed here.  Each specific row adds its own name to
    this function when it lands, and ``tests/test_emit.py`` asserts over the whole
    bundle that no document is claimed twice.
    """
    return is_enum_root(doc) or isinstance(doc.get("allOf"), list) or union_root(doc)


def is_object_root(doc: dict) -> bool:
    """D2's object row: a plain object root -- ``properties``, and no kind of its
    own that a specific row owns."""
    return (
        "properties" in doc
        and doc.get("type") in (None, "object")
        and not declares_its_own_root_kind(doc)
    )


def is_scalar_root(doc: dict) -> bool:
    """D2's root-scalar row: a root whose ``type`` names one scalar, and NOT an
    enumeration.

    ``"enum" not in doc`` is the load-bearing clause and not a belt: all 214 of the
    bundle's root enums declare ``type: "string"``, so without it the scalar row and
    the enumeration row claim the same 214 documents and the table has an ambiguity
    at a sixth of the population.
    """
    return (
        isinstance(doc.get("type"), str)
        and doc["type"] in compiler.SCALAR
        and not declares_its_own_root_kind(doc)
    )


def is_enum_root(doc: dict) -> bool:
    """D2's enumeration row: the root itself carries an ``enum`` (step 3).

    A DIFFERENT predicate from step 3's population test :func:`carries_an_enum`,
    and it IMPLIES it -- the root carrying an enum is a node carrying an enum -- so
    the row cannot claim a document the step does not count.  That implication is
    the relationship and ``tests/test_enum.py`` asserts it over the whole bundle;
    the two are not interchangeable, because 535 documents carry an enum somewhere
    and only 214 carry one at the root.
    """
    return "enum" in doc

def is_container_root(doc: dict) -> bool:
    """Step 6's row, and step 6's population: a root that is a container.

    An array (D2's ``RootModel[list[X]]`` row), a mapping (an object declaring no
    property), or a multi-type node.

    **The exclusion is load-bearing and the lane's own count was over the predicate
    WITHOUT it.**  Measured both ways on the 3.2 bundle: the bare shape test selects
    37 documents (32 mappings, 5 arrays, 0 multi-type), and 28 of those 32 mappings
    declare a union at the root as well -- so without the clause ``union_root`` and
    this row both claim all 28.  The union owns them for the reason
    :func:`declares_its_own_root_kind` states: a root ``oneOf`` makes the document a
    union whatever else the root declares.  With it, this row's population is 9 (5
    arrays, 4 mappings), overlapping neither :func:`is_leaf_object` nor
    :func:`references_a_property` in a single document.
    """
    kind = doc.get("type")
    if declares_its_own_root_kind(doc):
        return False
    if isinstance(kind, list):
        return True
    return kind == "array" or (kind == "object" and "properties" not in doc)


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


def carries_an_enum(doc: dict) -> bool:
    """Step 3's population: an ``enum`` at a SCHEMA POSITION anywhere in it.

    Root and inline together, because D2 gives both the same row and the lowering
    makes no distinction -- 214 of the bundle's documents carry one at the root
    and 535 carry one somewhere, over 1,069 enum nodes.

    Position is the whole of it, which is why this reads ``nodes`` rather than
    searching for the key: an ``enum`` holds INSTANCE data, so a value inside one
    may itself be an object with a property named ``enum``, and a blanket walk
    would count a document that has none.  ``emit.is_enum_root`` is the narrowing
    of this to the root, and implies it.
    """
    return any("enum" in n for _, n in nodes(doc))


def composes_at_the_root(doc: dict) -> bool:
    """Step 4's population: a root carrying ``allOf`` with NO union beside it.

    **301 documents**, and the definition is what lands on that number: the other
    readings give 342 (any root ``allOf``, union or not), 401 (``allOf`` anywhere
    in the document) and 257 (``allOf`` at the root and nowhere else).  A verdict
    read off a population nobody counted is a verdict over however many documents
    there turned out to be.

    The union clause is not a convenience: a ``oneOf``/``anyOf`` root is step 5's
    row whatever ELSE it carries, because the root ``allOf`` of a draft-07
    document applies to the whole instance and therefore to every branch, and a
    row that lowered the conjuncts without the branches would apply the bases to
    some branches and not others.  So the two populations are DISJOINT by this
    clause and ``emit.lower_document`` fails on a document two rows select rather
    than letting a table order decide.

    **"A union beside it" IS :func:`union_root`, and reading it any other way left
    a 14-document hole in the partition.**  This clause used to ask whether the key
    ``oneOf`` or ``anyOf`` was PRESENT, while ``union_root`` asks the lowering
    (``union.keyword`` plus ``rules.presence_only``) and answers no for a
    combinator of ``required`` GROUPS -- which is a rule on one class, not a union
    of shapes.  So a root carrying ``allOf`` beside a presence-only ``anyOf`` was
    refused by this row for having a union and by step 5's row for not having one,
    and ``emit.lower_document`` reported "no D2 row selects this root" for all 14
    of them.  Those 14 were 14 of the 21 documents ``salesagent-j3k2l.21`` was
    filed over.

    The fix is the one ``union_root``'s own docstring already states for the other
    direction -- ONE implementation of the keyword read, and it is the LOWERING'S.
    Measured over all 1,054 portable documents: 287 -> 301, **0 documents lost**,
    and **0 of the 301 claimed by any other row**, so the table is still a
    partition.

    This is the row's selector and the predicate its metric is stated over, so it
    cannot come to claim a document the step does not count.
    """
    return isinstance(doc.get("allOf"), list) and not union_root(doc)


def union_root(doc: dict) -> bool:
    """Step 5's population: a document whose root carries ``oneOf`` or ``anyOf``.

    156 of the 3.2 bundle's 1,054 portable documents, and 0 of them carry both.

    ONE implementation of the keyword read, and it is the LOWERING'S:
    ``lower.union.keyword`` is what the lowering reads the keyword with, and this
    selector is built on that same function, so a row cannot come to claim a
    document the selector does not count.  The lane had it the other way round --
    the function here and the lowering importing this module -- which D13's import
    rule forbids; ``bundle`` -> ``lower`` is the direction that works, and
    ``states_an_object_rule`` reads ``rules.presence_only`` the same way.
    """
    # A combinator of ``required`` GROUPS is not a union, and that clause is the
    # step-5/step-7 boundary.  A branch declaring no property has no shape to
    # subclass -- ``lower.union._plan`` refuses exactly that -- so such a root is a
    # rule on one class (D6) and step 7's lowering reads it inside
    # ``compiler.lower_object``.  Measured: all 5 of the bundle's presence-only roots
    # were claimed by this row and by none other, so step 7's whole population was
    # selected by a row that refuses it.  Both readings are each step's own --
    # ``union.keyword`` and ``rules.presence_only`` -- and they meet HERE because a
    # lowering cannot import another lowering (D13).
    kw = union.keyword(doc)
    return kw is not None and not rules.presence_only({kw: doc[kw]})


def _is_property_or_items(pointer: str) -> bool:
    parts = [p for p in pointer.split("/") if p]
    if not parts or parts[0] != "properties":
        return False
    return len(parts) == 2 or (len(parts) == 3 and parts[2] == "items")


def states_an_object_rule(doc: dict) -> bool:
    """Step 7's population: an object root whose composition is a rule about PRESENCE.

    The three clauses, and each one is what makes this selector DISJOINT from another
    step's rather than a matter of precedence -- a document two rows select is a build
    failure, so the disjointness has to be a property of the predicates and not a
    convention:

    * no ``$ref``, ``allOf``, ``definitions`` or ``$defs`` anywhere.  That is steps 2
      and 4 and a later row, and it is also what keeps this out of
      :func:`references_a_property`, which selects on a reference EXISTING.
    * at least one ``if``/``then``/``else``/``not``/``oneOf``/``anyOf``.  Those six are
      exactly the keywords :func:`is_leaf_object` excludes, so a document satisfying
      this clause is not step 1's.  ``dependencies``, ``min``/``maxProperties`` and
      ``uniqueItems`` do NOT appear in that clause on purpose: ``is_leaf_object``
      already selects a document carrying only those, so claiming one here would be
      the two-rows failure.  ``core/format-id.json`` is such a document -- step 1's
      row, refused there until this step, emitted there now.
    * every combinator in it is ``required``-only (``rules.presence_only``).  That is
      the step-5 boundary: a combinator of SHAPES is a union root and step 5's, a
      combinator of ``required`` groups has no shape to subclass and is a rule.  The
      test is the lowering's own reading, so a row cannot claim a document its step
      cannot lower.
    """
    if "properties" not in doc or doc.get("type") not in (None, "object"):
        return False
    kw = schema_keywords(doc)
    if kw & {"$ref", "allOf", *DEFINITIONS}:
        return False
    if not kw & {*CONDITIONAL, "oneOf", "anyOf"}:
        return False
    return all(rules.presence_only(n) for _, n in nodes(doc))
