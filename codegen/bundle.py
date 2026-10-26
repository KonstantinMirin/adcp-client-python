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

import copy
import json
from collections.abc import Collection, Iterator, Mapping
from pathlib import Path
from typing import NamedTuple

from adcp.types._base import applied_schema

from codegen import keywords
from codegen.refusal import Kind, Refusal

#: Top-level directories holding projections of documents published elsewhere.
PROJECTIONS = ("bundled", "mcp")
#: Files describing the bundle, not a message.
REGISTRY = ("index.json", "manifest.json", "manifest.schema.json")


def escape_key(key: str) -> str:
    """One JSON Pointer segment from a document KEY (RFC 6901's two escapes).

    **In the SOURCE layer, which is where ``docs/plan/architecture.md`` §11 puts it**:
    this module knows "files, paths, ``$ref`` URIs, edges, the record", and a pointer
    segment is the spelling of a path into a document.  It was in ``compiler.py`` --
    the walk -- and that was the one import ``codegen/harness.py`` made of the walk,
    which §9 forbids the verifier outright (``tests/test_import_rule.py``'s
    ``VERIFIER_MAY_IMPORT``).  §14 step 5 is the row that moves it, because the move is
    only correct once this module imports no LOWERING: it did, for the root selectors
    this row deletes, so ``import codegen.bundle`` reached ``codegen.lower`` and trading
    the named import for that reach would have bought the ratchet a line and cost §9 its
    point.

    One speller, because a pointer segment is spelled by FOUR readers --
    :func:`subschemas`, ``harness._nodes``, ``harness.compare_schema``'s property
    descent, and the mapping row's ``patternProperties`` pointer -- and the inverse is
    beside it (:func:`node_at`).  A ``patternProperties`` expression is the first key in
    this bundle that actually NEEDS it: the ``media-buy/get-products-response.json``
    extension pattern is ``^https?://[^@]+@sha256:[a-f0-9]{64}$``, whose two slashes
    would otherwise read as two pointer hops and make the refusal's own pointer
    undereferenceable.
    """
    return key.replace("~", "~0").replace("/", "~1")


def node_at(root: object, pointer: str) -> object:
    """The node a JSON Pointer names in ``root``.  The INVERSE of :func:`escape_key`.

    Beside its inverse for the same reason that one is here: a pointer segment is
    spelled and read by more than one module, and :func:`record` dereferences the
    fragment half of a ``$ref`` while ``harness.at`` dereferences a pointer on the
    document side.  Two readings of RFC 6901's two escapes is how an inliner and a
    grader come to disagree about which node a reference names.

    Raises ``KeyError``, ``IndexError``, ``TypeError`` or ``ValueError`` for a pointer
    that names no node, which is what lets :func:`record` turn one into a refusal
    naming the reference rather than letting it crash the run.
    """
    cur = root
    for part in pointer.lstrip("/").split("/"):
        if part == "":
            continue
        part = part.replace("~1", "/").replace("~0", "~")
        # The two containers a JSON Pointer hop can land in, each matched before it is
        # indexed.  The hop used to be one expression with an ``isinstance(cur, list)``
        # guard and a ``# type: ignore[index]`` for the other half, which says "this is
        # not indexable and index it anyway" -- the suppression §14 step 6 admits none
        # of.  A ``match`` states both arms and the ELSE is what the docstring already
        # promises: a pointer naming no node raises, and ``record`` is what turns one
        # into a refusal naming the reference.
        match cur:
            case list():
                cur = cur[int(part)]
            case dict():
                cur = cur[part]
            case _:
                raise TypeError(
                    f"{pointer!r}: the hop {part!r} is taken on a "
                    f"{type(cur).__name__}, which names no node"
                )
    return cur


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
# the one descent: which keys hold a subschema, and the position each one holds it at
# --------------------------------------------------------------------------- #
#: The table's descent column, which is the ONE descent table
#: (``docs/plan/architecture.md`` §11) and which this module is one of the named
#: readers of.  Descend only where a subschema can legally appear: ``examples``,
#: ``default``, ``const`` and ``enum`` hold INSTANCE data, so a key named ``$ref`` or
#: ``allOf`` beneath one of them is a data field whose name collides, and a blanket
#: walk reports a composition the document does not have.
#:
#: Read at ROOT and used at every position, which is a fact about the table rather
#: than an assumption: measured over all nine positions, the column is the same
#: fifteen keywords with the same child position at each one.  A row that ever
#: differed would make this a per-position read, not a second table.
_DESCENDS = keywords.descends_at(keywords.Position.ROOT)

#: Of those keywords, the ones whose subschemas are reached THROUGH A NAME, and the
#: ones that hold a LIST of them.  Everything else in the column holds exactly one
#: subschema.  This is draft-07's GRAMMAR -- how the keyword spells what it holds --
#: and not one of the table's decisions, which is why the SET of descending keywords
#: is read above and never restated here.
#:
#: Derived from the child POSITION wherever the position decides it: a PROP value and
#: a DEF entry are each reached through a name, and a BRANCH or a CONJ is one of a
#: list.  MAPV is the one position two keywords reach by different spellings --
#: ``patternProperties`` holds pattern → schema there and ``additionalProperties``
#: holds one schema -- so that one name is written, and it is the only one.
_HELD_BY_NAME = frozenset(
    {k for k, p in _DESCENDS.items() if p in (keywords.Position.PROP, keywords.Position.DEF)}
    | {"patternProperties"}
)
_HELD_IN_A_LIST = frozenset(
    k for k, p in _DESCENDS.items() if p in (keywords.Position.BRANCH, keywords.Position.CONJ)
)

#: The combinators and the conditionals, READ OFF the declaration's descent column
#: rather than named: a combinator holds subschemas at a BRANCH or a CONJ and a
#: conditional holds one at a RULE, which is what each one IS.  Two literals before
#: this, and a keyword joining either family had to be written here as well as in the
#: table (``docs/plan/architecture.md`` §11: the descent column is the one owner).
COMPOSITION = tuple(sorted(_HELD_IN_A_LIST))
CONDITIONAL = tuple(k for k, p in _DESCENDS.items() if p is keywords.Position.RULE)
#: The two keywords holding a bag of named subschemas, READ OFF the declaration's
#: descent column rather than named: they are the keywords whose subschemas occupy a
#: DEF position, which is what a definitions section IS.  ``compiler.check_keywords``
#: admits them at every node from the same table and the selectors below exclude a
#: document declaring one, so there is no literal here for the pair to drift from.
DEFINITIONS = frozenset(k for k, p in _DESCENDS.items() if p is keywords.Position.DEF)


def subschemas(node: Mapping) -> Iterator[tuple[str, str, object, keywords.Position]]:
    """Every subschema ``node`` holds: ``(keyword, pointer suffix, subschema, position)``.

    THE ONE DESCENT STEP of this module, and both readers of it need the same answer:
    :func:`nodes` walks it to build the censuses, and :func:`record` rebuilds along it
    to place a reference's target.  A walk and an inliner that descended by two sets
    would disagree about which ``$ref`` is a reference at all, which is the defect the
    table's descent column exists to remove.

    The pointer suffix is what reaches the subschema from ``node`` -- ``/properties/x``,
    ``/allOf/0``, ``/items`` -- with a key escaped by RFC 6901's two escapes
    (:func:`escape_key`), and the position is the one the table says the keyword
    holds its subschemas at.

    In the NODE'S OWN KEY ORDER and not the table's, because :func:`references` states
    its result is in document order and the run reads the first of them by name.
    """
    for keyword, held in node.items():
        position = _DESCENDS.get(keyword)
        if position is None:
            continue
        if keyword in _HELD_BY_NAME:
            if isinstance(held, dict):
                for key, sub in held.items():
                    yield keyword, f"/{keyword}/{escape_key(key)}", sub, position
        elif keyword in _HELD_IN_A_LIST:
            if isinstance(held, list):
                for i, sub in enumerate(held):
                    yield keyword, f"/{keyword}/{i}", sub, position
        elif isinstance(held, list):
            # A draft-07 ``items`` may be a TUPLE of schemas, and nothing else in the
            # column spells a list it is not already read as one for.
            for i, sub in enumerate(held):
                yield keyword, f"/{keyword}/{i}", sub, position
        elif isinstance(held, dict):
            yield keyword, f"/{keyword}", held, position


def nodes_at(
    node: object,
    pointer: str = "",
    position: keywords.Position = keywords.Position.ROOT,
) -> Iterator[tuple[str, dict, keywords.Position]]:
    """Every ``(JSON Pointer, subschema, POSITION)`` at a schema position.

    **The POSITION is the descent column's own answer and is never recovered from the
    pointer string.**  ``docs/plan/architecture.md`` §6: the position is assigned from
    the structural keyword descended through, so no reader derives it from a pointer --
    and the readings that did were a measured defect in both directions.  A pointer
    segment reading ``then`` is a conditional only at a KEYWORD position, and a scan
    for one missed ``not`` entirely, which is the other half of §3's RULE position.

    ``position`` is the root's by default, which is the one position no keyword
    descends into.  The nine are §3's and the column is :func:`subschemas`'.
    """
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from nodes_at(v, f"{pointer}/{i}", position)
        return
    if not isinstance(node, dict):
        return
    yield pointer, node, position
    for _, suffix, sub, held_at in subschemas(node):
        yield from nodes_at(sub, f"{pointer}{suffix}", held_at)


def nodes(node: object, pointer: str = "") -> Iterator[tuple[str, dict]]:
    """Every ``(JSON Pointer, subschema)`` at a SCHEMA POSITION in the document.

    The one walk.  ``schema_keywords`` and ``references`` are both read off it, so
    the two censuses cannot come to disagree about what a schema position is --
    which is the same reason ``harness`` declares its descent tables beside both
    of its walks.  It descends by :func:`subschemas`, so the walk and
    :func:`record`'s inliner read one declaration of what a schema position is.

    The POSITION-carrying form is :func:`nodes_at`, and this is it with the position
    dropped rather than a second walk: a reader that does not ask where a node is
    should not have to pass the root's position in to find out.
    """
    for pointer_, node_, _ in nodes_at(node, pointer):
        yield pointer_, node_


def schema_keywords(node: object) -> set[str]:
    """Every key appearing at a SCHEMA POSITION anywhere in the document."""
    return {k for _, n in nodes(node) for k in n}


def references(node: object) -> list[tuple[str, str, keywords.Position]]:
    """Every ``(pointer, $ref, POSITION)`` at a schema position, in document order.

    **The position is carried, and a reader that needs to know whether the walk
    LOWERS a reference is why.**  ``docs/plan/rebuild-plan.md`` §3: "RULE is the
    position that changes a keyword's meaning most: under a conditional, a keyword
    describes what a rule TESTS, not what an instance must be, so no type is lowered
    from it" -- so a ``$ref`` at RULE emits no import and its target is legitimately
    absent from the run.  Without the position this list cannot tell such a reference
    from a PROP one, which is the repetition §11 names: one descent table, read by
    the parser, by this module and by the verifier's record walk.

    :func:`lowered_references` is the derived reading; this is the census.
    """
    return [(p, n["$ref"], at) for p, n, at in nodes_at(node) if isinstance(n.get("$ref"), str)]


def lowers_no_type(node: object) -> frozenset[str]:
    """The pointers of this document that NO TYPE is lowered from.

    ``docs/plan/rebuild-plan.md`` §3's RULE position, read transitively: a node inside
    ``not``, ``if``, ``then`` or ``else`` describes what a rule TESTS, so no type is
    lowered from it -- and nothing BELOW such a node is lowered either, because
    ``lower/rules.py`` is the rule source's only reader and it reads no reference, no
    format and no nested shape.  The walk never arrives there at all.

    Derived from :func:`nodes_at`, so the answer is the descent column's and the
    transitivity is the walk's: a child of a RULE node is reached THROUGH the RULE hop,
    whatever its own position then is.  Read off pointer segments instead -- which two
    readers did -- it is wrong in both directions: a property legitimately named
    ``then`` is not a conditional, and a scan for ``if``/``then``/``else`` misses
    ``not``.
    """
    out: set[str] = set()

    def walk(held: object, pointer: str, tested: bool) -> None:
        if isinstance(held, list):
            for i, item in enumerate(held):
                walk(item, f"{pointer}/{i}", tested)
            return
        if not isinstance(held, dict):
            return
        if tested:
            out.add(pointer)
        for _, suffix, sub, at in subschemas(held):
            walk(sub, f"{pointer}{suffix}", tested or at is keywords.Position.RULE)

    walk(node, "", False)
    return frozenset(out)


def lowered_references(doc: dict, named: Collection[str]) -> list[tuple[str, str]]:
    """The ``(pointer, $ref)`` pairs the WALK LOWERS a type or an import from.

    The closure claim ranges over THIS and not over :func:`references`, and the
    difference is two of the design's own sentences rather than a narrowing:

    * **§3's RULE position.**  No type is lowered from a node under a conditional, so
      such a reference emits no import and its target is legitimately not emitted.  The
      live case is ``core/forecast-dimension-geo.json`` referencing
      ``core/postal-country-system.json`` at ``/allOf/3/then/anyOf/0``: the emitted
      module imports nothing from the target, and the target is refused.
    * **§5's ``definitions`` row, read by :func:`reaches`.**  A section is "nothing by
      itself" and an entry "nothing references is not declared", so a reference inside a
      dead entry is at a position no class names and no assertion descends into.

    ``named`` is :func:`named_nodes` for this document -- the on-demand declaration set
    -- which is the same argument :func:`undecidable_references` takes and for the same
    reason.  Neither clause is a hand-written document set, which is the defect §9 names:
    both are predicates over the document's own structure.
    """
    tested = lowers_no_type(doc)
    entries = section_entries(doc)
    return [
        (pointer, uri)
        for pointer, uri, _ in references(doc)
        if pointer not in tested and reaches(pointer, entries=entries, declared=named)
    ]


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


class Edge(NamedTuple):
    """One ``$ref``: where it is written, and what it names.

    ``docs/plan/architecture.md`` §4 names this the source layer's own export -- "the
    reference graph over the bundle (``edges``: every ``(document, pointer, target
    document, target pointer)``, read off the raw mappings by the table's descent
    column)" -- and §10 is what asks for it: the run "reads the reference edges off the
    bundle (``bundle.edges``), takes the transitive closure of the named documents over
    them ... orders the closure so every document follows the documents it references".

    **ONE SCAN of the bundle, and three readings of it.**  :func:`named` is §10's
    per-document ``named`` set, :func:`composed` is the pointers another document's root
    ``allOf`` composes, and the run derives the graph from the same tuples.  The three
    were two scans and a closure walked lazily through a binder, and each read its own
    answer off the bundle; a scan per question is how two of them come to disagree about
    which ``$ref`` is a reference at all (§11's descent-table row).

    :attr:`position` is the descent column's own answer and is never recovered from the
    pointer string (§6), and :attr:`conjunct_of_root` is the same fact one hop up: the
    referring node is an entry of the DOCUMENT ROOT's ``allOf`` list, which
    :func:`subschemas` is what says.  A reader asking either from the spelling of
    ``pointer`` would be the reading §6 removed.
    """

    #: The referring document, bundle-relative.
    document: str
    #: The referring node's JSON Pointer inside :attr:`document`.
    pointer: str
    #: The position the referring node sits at.
    position: keywords.Position
    #: The ``$ref`` exactly as the document writes it.
    uri: str
    #: ``True`` where the document half is empty: a pointer into :attr:`document`
    #: itself, which resolves against the referrer and names no other document.
    local: bool
    #: The bundle document the URI's document half names, or ``None`` where it names
    #: none.  ``None`` for a local reference too, whose target IS :attr:`document`.
    target: str | None
    #: The pointer half, ``""`` for a reference naming a root.
    into: str
    #: The referring node is an entry of the document ROOT's ``allOf`` list.
    conjunct_of_root: bool


def edges(bundle_dir: Path) -> tuple[Edge, ...]:
    """Every reference in the bundle, in (document, document-order) order.

    Reads every portable document ONCE.  Sorted by document, like :func:`portable` (P7),
    and in each document's own order, because :func:`references` states its result is in
    document order and the run reads the first of them by name.
    """
    known = set(portable(bundle_dir))
    out: list[Edge] = []
    for document in sorted(known):
        doc = read(bundle_dir, document)
        # The root's own ``allOf`` entries, by the descent step and not by the spelling
        # of a pointer: :func:`composed` asks which nodes another document's ROOT
        # composes, and "of the root" is one hop of :func:`subschemas`.
        conjuncts = {
            suffix
            for keyword, suffix, _, _ in subschemas(doc)
            if keyword == "allOf"
        }
        for pointer, uri, position in references(doc):
            head, into = split_ref(uri)
            out.append(
                Edge(
                    document=document,
                    pointer=pointer,
                    position=position,
                    uri=uri,
                    local=not head,
                    target=document_for(head, known) if head else None,
                    into=into,
                    conjunct_of_root=pointer in conjuncts,
                )
            )
    return tuple(out)


def named(found: Collection[Edge]) -> dict[str, frozenset[str]]:
    """§10's per-document ``named`` set: the pointers of a document's nodes that a
    ``$ref`` NAMES, keyed by the document the reference RESOLVES AGAINST.

    :func:`named_nodes`' rule, read off :func:`edges` rather than off a scan of its own.
    """
    out: dict[str, set[str]] = {}
    for edge in found:
        if not edge.into:
            continue
        # An absolute fragment reference asks of the document its own half names; a
        # LOCAL one asks of the REFERRING document, because that is what a pointer with
        # no document half means.
        document = edge.document if edge.local else edge.target
        if document is not None:
            out.setdefault(document, set()).add(edge.into)
    return {d: frozenset(p) for d, p in out.items()}


def composed(found: Collection[Edge]) -> dict[str, frozenset[str]]:
    """For each document, the pointers of its nodes that another document's root
    ``allOf`` COMPOSES.

    The companion to :func:`named`, and the same kind of fact: a function of the BUNDLE
    and not of the run's document set, so a module's ``__all__`` does not depend on who
    else was emitted (P7) and the one-document command writes the bytes the
    whole-population run writes.  ``emit.exported`` says what it is for -- a composing
    subclass re-uses the base's decided field, so the base's field types cross the
    module boundary while no ``$ref`` fragment names them.

    A bare conjunct composes the target's ROOT, whose pointer is ``""``; the one
    conjunct in this bundle that carries a fragment
    (``core/package-delivery-metric-value.json`` -> ``core/delivery-metric-aggregate.json#/oneOf/0``)
    composes that node, and it is recorded at its own pointer rather than folded into the
    root -- a branch's fields are not the union base's.  A LOCAL conjunct composes a node
    of its own document, whose symbol that module declares and never imports, so it is
    that document's own entry -- the same reason :func:`named` keys a local reference
    against the referring document.

    **It was ``emit._composed_nodes`` and §11 puts it here**, in the layer that knows
    "files, paths, ``$ref`` URIs, edges, the record".  It read every portable document a
    SECOND time, after the ``named_nodes`` pass -- ~2 s on the 3.2 bundle -- and the
    merge of the two scans its docstring named as the upgrade path is :func:`edges`:
    both readings are now projections of one scan.  The clause the predicate it asked
    before carried -- "a root ``allOf`` and no union beside it" -- is empty for this
    question: measured over the 1,054 portable documents, the pairs a root ``allOf``
    names are the same 27 either way, because ``union.ROOT_CONJUNCTS`` refuses a union
    root carrying ``allOf``, so such a root never composes and its conjuncts' fields
    never cross a module boundary.
    """
    out: dict[str, set[str]] = {}
    for edge in found:
        if not edge.conjunct_of_root:
            continue
        document = edge.document if edge.local else edge.target
        if document is not None:
            out.setdefault(document, set()).add(edge.into)
    return {d: frozenset(p) for d, p in out.items()}


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

    **:func:`named` is the rule and this is the scan**, kept as the one-argument
    spelling for a caller that holds a bundle directory and not an edge list.  §10 reads
    it as ``bundle.named(edges)``, so the run scans once and this does not run inside it.
    """
    return named(edges(bundle_dir))


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


def _is_an_annotation(key: str, position: keywords.Position) -> bool:
    """Does this sibling of a ``$ref`` state nothing about ACCEPTANCE?

    The one question :func:`record` asks of a sibling, and the answer decides which
    side wins where the referring node and its target both state the key.  Read off
    the TABLE's effect column rather than from a set of annotation names, which §11
    names as one of today's repetitions: an annotation is a key whose cell compiles to
    no type, no field and no rule, which is what "states nothing about acceptance"
    IS.  A key in the ``x-`` namespace with no row of its own is one too -- §6 admits
    it by prefix -- and a key with no row and no prefix is not: the screen refuses the
    document on it, and until then the target's value is the one the draft holds.
    """
    answer = keywords.cell(key, position)
    if answer is None:
        return keywords.admitted_by_prefix(key)
    return answer.effect not in keywords.COMPILES and answer.effect is not keywords.Effect.REFUSE


def _beside(placed: dict, referring: Mapping, position: keywords.Position) -> dict:
    """The inlined copy with the referring node's own keys kept beside it.

    ``docs/plan/architecture.md`` §4, and §13 item 2 is where the two halves of it
    were settled:

    * **no key is dropped**, on either side.  §3 of the semantics document forbids it,
      so every key of the referring node other than the ``$ref`` itself is in the
      result whether the target states it or not.
    * **an ANNOTATION sibling's referring value wins.**  §5's ``$ref`` row says the
      sibling's description wins, and an annotation states nothing about acceptance, so
      it cannot disagree with the draft.
    * **a CONSTRAINING sibling's referring value does NOT win.**  Draft-07 ignores
      every sibling of a ``$ref``, so the document's accepted set at this node is the
      target's alone; letting the referring value win would make the record state an
      acceptance fact the bundle's own draft does not hold, which is §3's
      canonicalisation and §9's last rule.  The key is kept, the target's value stands
      where both state one, and the cell says the keyword compiles to nothing at this
      co-occurrence so §8 does not grade it.

    Measured over the 3.2 bundle's raw documents: **0 constraining siblings**.  The
    only keys ever beside a ``$ref`` are ``description`` (1,158 sites), ``title`` (62),
    ``default`` (37), ``deprecated`` (36), ``$schema`` (1) and five ``x-`` keys (26),
    and every one of them is an annotation by the test above.  So the second clause has
    no site today and is written because the rule is the document's, not because a site
    asks for it -- a document adding a constraining sibling gets the draft's answer
    rather than this inliner's.
    """
    siblings = {k: copy.deepcopy(v) for k, v in referring.items() if k != "$ref"}
    wins = {k: v for k, v in siblings.items() if k not in placed or _is_an_annotation(k, position)}
    return {**placed, **wins}


class _Where(NamedTuple):
    """Where in the reference graph one inlining step stands: the two cycle guards.

    Both are a PATH and not a visited set, because a diamond is not a cycle: two
    references to one target each get their own copy (§4 says a deep copy per
    reference), so meeting a document twice on different paths is the record's normal
    shape and only meeting it twice on ONE path is undefined.
    """

    #: The cross-document hop path, starting at the document whose record this is.
    chain: tuple[str, ...]
    #: The ``(document, pointer)`` pairs of the local references already open inside the
    #: copy being taken.  Empty outside a copy, since a local reference is left alone
    #: there and so is never followed.
    anchors: tuple[tuple[str, str], ...]


def record(bundle_dir: Path, document: str) -> dict | Refusal:
    """THE DOCUMENT OF RECORD: ``document`` with every cross-document ``$ref`` inlined.

    This package's own inliner (``docs/plan/architecture.md`` §4), and it does what §3
    of the semantics document says and nothing else.  Resolution INLINES; it does not
    rewrite.  No keyword is dropped, derived, reordered or restated in another spelling,
    on the referring node or on the inlined target.

    THE SELF-CONTAINED FORM, and both consumers need exactly it:

    * ``AdCPBaseModel.strict_validate`` decides acceptance against the document the
      emitter wrote into the package beside the module, which is the one its class names
      on ``__adcp_schema__`` (D4).  The RAW document of a referencing class is not
      decidable there: ``jsonschema`` meets an absolute ``$ref``, finds no store, and
      FETCHES IT OVER THE NETWORK -- measured at 4.4 s per validation against a live
      URL, on a code path ``jsonschema`` deprecates and says "will shortly become an
      error".  Offline it raises instead.  So the package carries this.
    * ``check_pair``'s whole input is a document with no cross-document reference left
      in it, and §8 compares against the document rather than against any
      canonicalisation of it.

    *Why our own, and what it replaced.*  This was ``hypothesis_jsonschema``'s resolver,
    which CANONICALISES while it inlines: it writes a finite type out as its members
    (``{"type": "boolean"}`` → ``{"enum": [false, true]}``), rewrites
    ``additionalProperties: false`` into ``{"not": {}}``, drops a redundant
    ``additionalProperties: true``, respells a one-member ``enum`` as a ``const``,
    derives a ``maxItems`` from a ``uniqueItems``, reduces an enum node to its members
    and drops every annotation at it, and rewrites a root ``if``/``then`` into an
    ``anyOf`` of the two cases with the node's ``title`` copied into both.  Every one of
    those writes a document the bundle does not state, and every reader downstream then
    needed a fold to undo it -- six of them in the verifier, which §9 deletes with this.
    An inliner that changes nothing needs none.  The payload generator's resolver stays
    where §4 confines it, drawing payloads in the accepts check, where it may
    canonicalise its own copy because that copy is an instrument of one check and is not
    the document.

    **The four rules, each one §4's:**

    * every cross-document ``$ref`` is replaced by a DEEP COPY of the node its pointer
      names, so two references to one target cannot alias into each other;
    * the referring node's own keys are kept beside the copy (:func:`_beside`);
    * a LOCAL ``$ref`` of this very document is left exactly as written.  It names a
      node of the document the package carries, so ``jsonschema`` resolves it against
      the referrer and fetches nothing;
    * a copy taken from document D has its OWN local references inlined from D before
      it is placed, **because it is leaving D's root scope**.  ``#/definitions/x`` in
      the copy would otherwise be read against the REFERRING document's root, where it
      names a different node or none.

    **Two shapes make the record undefined and return a** :class:`Refusal` **(VERDICT)
    rather than a mapping**, which is §4's own answer: a reference whose target is not a
    bundle document -- or is, and names no node of it -- and a cross-document cycle.
    Each is an obstruction of the POINTER SPACE or of the document, which is what §9
    makes a verdict rather than a deferral: there is no code to write that would clear
    it.  Measured on the 3.2 bundle: 0 of the 814 absolute references miss a document,
    0 of the 76 fragment pointers miss a node, and 0 cross-document cycles, so neither
    arm has a site and both are written because the record is undefined there.

    The kind is minted HERE and not read from ``compiler.kind_for``, and the two answer
    different questions: ``kind_for`` asks what the TABLE decides about a keyword, and
    its answer for ``$ref`` is DEFERRED at every position because the cell is a lowering
    effect the handler claims.  Nothing about this bundle's reference graph is in that
    cell.  Reading it would report a permanent obstruction as clearable work, which is
    §9's first rule run backwards.

    **A section IS descended, which the delegated resolver did not do.**
    ``resolve_all_refs`` descends its own ``SCHEMA_KEYS`` and ``SCHEMA_OBJECT_KEYS``,
    and ``definitions`` and ``$defs`` are in neither, so a reference under a section
    survived it.  This descends by the table's descent column (:func:`subschemas`),
    where a section's entry is a subschema at a DEF position, so "every cross-document
    ``$ref``" means every one.  ``undecidable_references`` therefore has fewer survivors
    to find, and that is an EMISSION change rather than a relaxation: the entry is still
    a position the package's own validation may decide through, and now the record
    decides it locally.

    KNOWN CEILING, unchanged in kind from the delegated resolver's: this is O(paths
    through the reference graph), because a fresh copy is placed per path, and the bundle
    holds a 9,109-byte document whose record is megabytes.  A cache keyed on
    ``(document, pointer)`` is not sound while :func:`_beside` lets a referring node
    contribute keys, so the cache's key would be the referring node too; nothing asks
    for it yet.
    """
    known = set(portable(bundle_dir))
    roots: dict[str, dict] = {document: read(bundle_dir, document)}

    def root_of(name: str) -> dict:
        if name not in roots:
            roots[name] = read(bundle_dir, name)
        return roots[name]

    def refuse(pointer: str, detail: str) -> Refusal:
        return Refusal("$ref", pointer, detail, kind=Kind.VERDICT)

    def placed(
        uri: str, *, pointer: str, home: str, scope: dict | None, where: _Where
    ) -> dict | Refusal | None:
        """The node a reference names, inlined and ready to be placed, or ``None`` where
        the reference STAYS as written.

        ``None`` is the one case §4 leaves alone: a LOCAL reference of the document whose
        record this is, which ``scope is None`` says we are at.
        """
        head, into = split_ref(uri)
        if not head:
            if scope is None:
                return None
            if (home, into) in where.anchors:
                open_now = " -> ".join(p for _, p in where.anchors)
                return refuse(
                    pointer,
                    f"{uri} closes a cycle of local references inside {home}, which is "
                    f"being copied out of its own root scope: {open_now} -> {into}",
                )
            root, at_home = scope, home
            where = _Where(where.chain, (*where.anchors, (home, into)))
        else:
            named = document_for(head, known)
            if named is None:
                return refuse(pointer, f"{uri} names no document of {bundle_dir}")
            if named in where.chain:
                return refuse(
                    pointer,
                    f"{uri} closes a cross-document reference cycle, which leaves the "
                    f"record undefined for {document}: {' -> '.join([*where.chain, named])}",
                )
            root, at_home = root_of(named), named
            where = _Where((*where.chain, named), ())
        try:
            target = node_at(root, into)
        except (KeyError, IndexError, TypeError, ValueError):
            return refuse(pointer, f"{uri} names no node of {at_home}")
        if not isinstance(target, dict):
            return refuse(
                pointer, f"{uri} names a {type(target).__name__} of {at_home}, not a schema"
            )
        return inline(target, pointer=pointer, home=at_home, scope=root, where=where)

    def inline(
        node: dict,
        *,
        pointer: str,
        home: str,
        scope: dict | None,
        position: keywords.Position = keywords.Position.ROOT,
        where: _Where = _Where((), ()),
    ) -> dict | Refusal:
        """``node`` with every reference under it inlined, or the first refusal reached.

        ``home`` is the document whose text this node is and ``scope`` is the root a
        local pointer in it resolves against -- ``None`` at the document whose record
        this is, where a local reference is left as written.  ``where`` carries the two
        cycle guards.
        """
        uri = node.get("$ref")
        if isinstance(uri, str):
            copied = placed(uri, pointer=pointer, home=home, scope=scope, where=where)
            if isinstance(copied, Refusal):
                return copied
            if copied is not None:
                return _beside(copied, node, position)
        done: dict[str, object] = {}
        for _, suffix, sub, at in subschemas(node):
            if not isinstance(sub, dict):
                continue  # not a schema; §3 drops nothing, so ``_rebuilt`` keeps it
            answer = inline(
                sub, pointer=f"{pointer}{suffix}", home=home, scope=scope, position=at, where=where
            )
            if isinstance(answer, Refusal):
                return answer
            done[suffix] = answer
        return {
            key: _rebuilt(key, value, done) if key in _DESCENDS else copy.deepcopy(value)
            for key, value in node.items()
        }

    return inline(
        roots[document], pointer="", home=document, scope=None, where=_Where((document,), ())
    )


def _rebuilt(keyword: str, held: object, done: Mapping[str, object]) -> object:
    """``held`` with each subschema replaced by the one :func:`record` inlined for it.

    The inverse of :func:`subschemas` for one keyword, and it rebuilds the keyword's own
    SPELLING: a map stays a map with its keys in their own order, a list stays a list of
    the same length, one schema stays one.  A value the descent did not reach -- an
    ``additionalProperties: false``, an ``items`` that is neither a schema nor a list of
    them -- is deep-copied as it stands, because §3 drops nothing and because a record
    that aliased the bundle's own object would let one reader's edit reach another's.
    """
    def done_or_copy(suffix: str, sub: object) -> object:
        return done[suffix] if suffix in done else copy.deepcopy(sub)

    if keyword in _HELD_BY_NAME and isinstance(held, dict):
        return {
            key: done_or_copy(f"/{keyword}/{escape_key(key)}", sub)
            for key, sub in held.items()
        }
    if isinstance(held, list):
        return [done_or_copy(f"/{keyword}/{i}", sub) for i, sub in enumerate(held)]
    if isinstance(held, dict):
        return done_or_copy(f"/{keyword}", held)
    return copy.deepcopy(held)


def pointers_above(pointer: str, candidates: Collection[str]) -> list[str]:
    """Those of ``candidates`` that are ``pointer`` itself or an ancestor of it.

    THE ONE PREFIX READING OF A JSON POINTER here, and both callers need it over a
    different collection: :func:`undecidable_references` asks it of the named pointers
    and of the section entries in the same breath.  A pointer is an ancestor when the
    next character is the separator, so ``/definitions/Text`` is not an ancestor of
    ``/definitions/TextArea`` -- which a bare ``startswith`` would call one.
    """
    return [c for c in candidates if pointer == c or pointer.startswith(f"{c}/")]


def section_entries(node: object) -> frozenset[str]:
    """Every pointer that names an ENTRY of a ``definitions`` / ``$defs`` section.

    Read off :func:`nodes` -- the one schema-position walk -- and not off the spelling
    of a pointer, because a segment reading ``definitions`` is a section only at a
    KEYWORD position.  ``/properties/definitions/properties/x`` is a property named
    ``definitions`` and the text cannot tell the two apart; the walk can, because it
    arrives at a property's value through ``properties`` and at a section's entry
    through the section.  The 3.2 bundle holds 0 such properties.  The difference is
    readable on a RAW document, which is what the censuses in ``tests/`` ask this of;
    in a RECORD a section is still a section -- :func:`record` descends one, so the
    references under it are inlined, but the entries themselves travel with the copy
    and a nested section is reachable at a pointer no document on disk spells.

    A section NESTED inside another node counts, which is why this is not limited to
    the root: resolution inlines a target's whole body, sections and all, so a carried
    document can hold an entry at ``/properties/x/definitions/y`` that no document on
    disk spells.
    """
    return frozenset(
        f"{pointer}/{kw}/{escape_key(key)}"
        for pointer, n in nodes(node)
        for kw in DEFINITIONS
        if isinstance(n.get(kw), dict)
        for key in n[kw]
    )


def reaches(pointer: str, *, entries: Collection[str], declared: Collection[str]) -> bool:
    """Is this position reached at all, from a class or from the document root.

    **VALIDATION AND THE LOWERING BOTH START AT A DECLARED POINTER AND DESCEND BY
    ASSERTION KEYWORDS, WHICH NEVER CROSS A SECTION BOUNDARY.**  ``reach`` is the
    DEEPEST declared pointer above this one -- the innermost class that grades or
    lowers through it -- or the document root when nothing declares one, since the root
    is always both.  The position is reached unless a ``definitions`` / ``$defs`` entry
    lies between ``reach`` and it, because crossing into one is the step no assertion
    takes.  An entry AT ``reach`` is not between them: there the declaration IS the
    entry, which is what section 5 means by declaring it on demand.

    ``entries`` is :func:`section_entries` for the document and ``declared`` is
    :func:`named_nodes` for it.  ONE implementation, because the two questions it
    answers are the same question: :func:`undecidable_references` asks whether a
    reference can be validated through, and ``tests/test_emit.lowered_nodes`` asks
    whether a node is lowered at all.  Two readings of one boundary is how a check and
    the emitter come to disagree about which positions exist.
    """
    reach = max(pointers_above(pointer, declared), key=len, default="")
    return not any(len(e) > len(reach) for e in pointers_above(pointer, entries))


def undecidable_references(
    resolved_doc: dict, named: Collection[str]
) -> list[tuple[str, str]]:
    """The references in a carried document that the package's own validation reaches.

    ``strict_validate`` decides acceptance against the document the emitter writes
    beside the module, so a reference AT A POSITION THAT VALIDATION REACHES is a schema
    nothing local can decide: ``jsonschema`` finds no store for an absolute URI and
    fetches the target over the network.  That is the obligation, and this is the
    predicate for it -- which is NARROWER than "the document holds a ``$ref``", in two
    ways that are each a rule stated elsewhere and not a relaxation:

    * A LOCAL reference is decidable.  It names a node of this very document, so the
      resolver resolves it against the referrer with no store at all, which is why
      :func:`resolved` leaves one in.
    * A reference inside a section entry NOTHING declares is never reached.  Section 5
      says a ``definitions`` / ``$defs`` section is "nothing by itself: a bag of named
      subschemas", each entry "declared on demand when a ``$ref`` names it"; section 3
      says "an entry nothing references is not declared".  So no class names a pointer
      inside such an entry and no enclosing node's assertions descend into one --
      draft-07 gives a section no assertion behaviour, which is the same fact
      ``compiler.local_reference`` reads when it declares an entry only where a
      reference names it, and that ``harness.compare_schema`` reads when it descends
      ``properties``, ``items``, ``propertyNames`` and a typed
      ``additionalProperties`` and not a section.

    **VALIDATION STARTS AT A DECLARED POINTER AND DESCENDS BY ASSERTION KEYWORDS, WHICH
    NEVER CROSS A SECTION BOUNDARY.**  That one sentence is the predicate.  For a
    reference, ``reach`` is the DEEPEST named pointer above it -- the innermost class
    that grades through it -- or the document root when nothing names one, since the
    root always grades.  The reference is reached unless a section entry lies between
    ``reach`` and the reference, because crossing into one is the step no assertion
    takes.  An entry AT ``reach`` is not between them: there the declaration is the
    entry, which is what section 5 means by declaring it on demand.

    ``named`` is :func:`named_nodes` for this document -- the on-demand set, the same
    one ``emit.lower_document`` is handed.  Measured over the 3.2 bundle's 101 remote
    references under a section: 77 in 18 documents sit in an entry some ``$ref`` names
    and are counted; 24 in ``a2ui/si-catalog.json``'s one dead section are not.  Of the
    bundle's 216 named pointers, 157 name a section entry exactly, 59 name a node under
    no section at all, and 0 name a node BELOW an entry -- so ``reach`` is today always
    either the entry itself or the root, and the deeper cases the sentence above decides
    are what keeps the rule from needing a second reading when they arrive.
    """
    entries = section_entries(resolved_doc)
    return [
        (pointer, uri)
        for pointer, uri, _ in references(resolved_doc)
        if split_ref(uri)[0] and reaches(pointer, entries=entries, declared=named)
    ]


# --------------------------------------------------------------------------- #
# the populations a step's result was stated over
# --------------------------------------------------------------------------- #
# **The six ROOT SELECTORS are gone, and so is the dispatch table they fed.**
# ``docs/plan/architecture.md`` §5: "Root and non-root are one path.  There is no
# second table of root selectors.  A document is ``parse(raw, position=ROOT)``
# followed by ``decide``."  §11's repetition table says the same thing from the
# other end -- "the kind read in ``_decide``, in the root selectors, in
# ``union.keyword``, in ``rules.presence_only`` | ``parse``'s classification" -- so a
# predicate here that read a ROOT'S KIND was the second reading of the one the walk
# makes per node.  ``is_object_root``, ``is_scalar_root``, ``is_enum_root``,
# ``is_container_root``, ``composes_at_the_root`` and ``union_root`` are deleted with
# ``emit.ROWS``, and ``declares_its_own_root_kind`` -- the disjointness clause that
# existed only to keep the table a partition -- with them.
#
# ``states_an_object_rule`` goes too, and for the OTHER half of §5's sentence: "the
# document-set predicates a step's result was stated over are the tests' business and
# live under ``tests/``."  It and the deleted selectors are now
# ``tests/populations.py``, which is also what lets this module import no LOWERING:
# ``union_root`` and ``states_an_object_rule`` were the two readers of
# ``lower.union.keyword`` and ``lower.rules.presence_only``, so ``import
# codegen.bundle`` reached eight ``codegen`` modules and now reaches two.  That is the
# measurement §14 step 5 owed ``tests/test_import_rule.py``: with the reach gone,
# :func:`escape_key` and :func:`node_at` move here and the verifier stops importing
# the walk.
#
# What stays are the three predicates that read a document's SHAPE rather than its
# root's kind, because the run itself reads them: ``is_leaf_object`` and
# ``references_a_property`` are the command in this package's own docstrings, and
# ``carries_an_enum`` is a census over schema positions.


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
    return bool(rs) and all(_is_property_or_items(p) for p, _, _ in rs)


def carries_an_enum(doc: dict) -> bool:
    """Step 3's population: an ``enum`` at a SCHEMA POSITION anywhere in it.

    Root and inline together, because D2 gives both the same row and the lowering
    makes no distinction -- 214 of the bundle's documents carry one at the root
    and 535 carry one somewhere, over 1,069 enum nodes.

    Position is the whole of it, which is why this reads ``nodes`` rather than
    searching for the key: an ``enum`` holds INSTANCE data, so a value inside one
    may itself be an object with a property named ``enum``, and a blanket walk
    would count a document that has none.
    """
    return any("enum" in n for _, n in nodes(doc))


def _is_property_or_items(pointer: str) -> bool:
    parts = [p for p in pointer.split("/") if p]
    if not parts or parts[0] != "properties":
        return False
    return len(parts) == 2 or (len(parts) == 3 and parts[2] == "items")


