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
import hashlib
import json
from collections.abc import Callable, Collection, Iterator, Mapping
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple

from adcp.types import _base
from adcp.types._base import applied_schema
from codegen import keywords
from codegen.refusal import BuildFailure, Kind, Refusal

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

    One speller, because a pointer segment is spelled by THREE readers --
    :func:`subschemas`, ``harness._nodes``, and the mapping row's
    ``patternProperties`` pointer -- and the inverse is beside it (:func:`node_at`).
    A ``patternProperties`` expression is the first key in
    this bundle that actually NEEDS it: the ``media-buy/get-products-response.json``
    extension pattern is ``^https?://[^@]+@sha256:[a-f0-9]{64}$``, whose two slashes
    would otherwise read as two pointer hops and make the refusal's own pointer
    undereferenceable.
    """
    return key.replace("~", "~0").replace("/", "~1")


def unescape_key(segment: str) -> str:
    """The document KEY one JSON Pointer segment spells.  :func:`escape_key`'s inverse.

    Beside its inverse for that function's own reason, and extracted from
    :func:`node_at`'s hop because a second reader arrived: ``harness.instance_path`` turns
    a pointer into the INSTANCE location it describes, and a key carrying a ``/`` has to
    come back out of the pointer the way ``node_at`` takes it out.  Two readings of RFC
    6901's two escapes is how a grader and a dereferencer come to disagree about which key
    a segment names.

    The order matters and is the inverse of :func:`escape_key`'s: ``~1`` first, then
    ``~0``, so a key spelling ``~1`` literally -- escaped ``~01`` -- does not come back as
    a ``/``.
    """
    return segment.replace("~1", "/").replace("~0", "~")


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
        part = unescape_key(part)
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


def package_roots(bundle: Path) -> frozenset[str]:
    """The documents whose own path is ALSO a directory of this bundle.

    ``docs/plan/architecture.md``, the layout rule beside ``write`` (2026-10-29): where
    the bundle holds both a document at path ``P`` and a directory at path ``P``, the
    two are one namespace and the document is its ROOT -- it emits ``P/__init__.py``
    and the directory's documents are its submodules.  ``brand.json`` beside ``brand/``
    is the one such pair in bundle 3.2.

    **A function of the BUNDLE and not of the run's document set**, which is the same
    requirement :func:`named_nodes` is written to and for the same reason (P7): a
    module whose PATH varied with which other documents were emitted would make
    ``brand.json``'s import spelling depend on whether anything under ``brand/``
    happened to be in the run.  So the directories are read off every portable
    document, including the ones that refuse -- a ``brand/`` holding nothing but
    refusals still makes ``brand.json`` the root of a package with one file in it,
    which is inert and importable, where the alternative is a name that moves.

    Every ANCESTOR is a directory too, so a document at ``a.json`` beside
    ``a/b/c.json`` is a package root even though nothing sits directly in ``a/``.
    """
    documents = portable(bundle)
    directories = {
        "/".join(PurePosixPath(d).parts[: i + 1])
        for d in documents
        for i in range(len(PurePosixPath(d).parts) - 1)
    }
    return frozenset(d for d in documents if d.removesuffix(".json") in directories)


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
DESCENDS = keywords.descends_at(keywords.Position.ROOT)

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
#:
#: **Public because the VERIFIER reads them** (``harness._DESCEND_MAP`` and its two
#: siblings), which §9 permits by name: ``codegen.bundle`` is in the verifier's import
#: set "for the record and the document set", and §9's own sentence is that the record
#: is read "by the verifier's own walk ... over the descent column of the table".  The
#: grammar is draft-07's spelling of what the column holds, so a second derivation of
#: it in the verifier would be a second reading of one grammar and would carry the one
#: written name (``patternProperties``) twice.
HELD_BY_NAME = frozenset(
    {k for k, p in DESCENDS.items() if p in (keywords.Position.PROP, keywords.Position.DEF)}
    | {"patternProperties"}
)
HELD_IN_A_LIST = frozenset(
    k for k, p in DESCENDS.items() if p in (keywords.Position.BRANCH, keywords.Position.CONJ)
)

#: The combinators and the conditionals, READ OFF the declaration's descent column
#: rather than named: a combinator holds subschemas at a BRANCH or a CONJ and a
#: conditional holds one at a RULE, which is what each one IS.  Two literals before
#: this, and a keyword joining either family had to be written here as well as in the
#: table (``docs/plan/architecture.md`` §11: the descent column is the one owner).
COMPOSITION = tuple(sorted(HELD_IN_A_LIST))
CONDITIONAL = tuple(k for k, p in DESCENDS.items() if p is keywords.Position.RULE)
#: The two keywords holding a bag of named subschemas, READ OFF the declaration's
#: descent column rather than named: they are the keywords whose subschemas occupy a
#: DEF position, which is what a definitions section IS.  ``compiler.check_keywords``
#: admits them at every node from the same table and the selectors below exclude a
#: document declaring one, so there is no literal here for the pair to drift from.
DEFINITIONS = frozenset(k for k, p in DESCENDS.items() if p is keywords.Position.DEF)


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
        position = DESCENDS.get(keyword)
        if position is None:
            continue
        if keyword in HELD_BY_NAME:
            if isinstance(held, dict):
                for key, sub in held.items():
                    yield keyword, f"/{keyword}/{escape_key(key)}", sub, position
        elif keyword in HELD_IN_A_LIST:
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


def named_values(node: Mapping[str, Any]) -> frozenset | None:
    """``node``'s ``const`` or ``enum`` as a set of scalars, or ``None`` for neither.

    Draft-07's own reading: a ``const`` is a one-member ``enum``.  ``None`` rather than
    the empty set, because "names no values" and "admits nothing" are different
    statements.  Scalars only, and a list with one non-scalar member contributes NOTHING
    rather than its scalar part -- a partial set would claim a disjointness the document
    does not state.
    """
    if "const" in node:
        value = node["const"]
        return frozenset({value}) if isinstance(value, (str, bool, int)) else None
    members = node.get("enum")
    if not isinstance(members, list) or not members:
        return None
    if not all(isinstance(member, (str, bool, int)) for member in members):
        return None
    return frozenset(members)


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


def declaring_site(
    bundle_dir: Path, known: Collection[str], edge: Edge
) -> tuple[Edge, str | None] | None:
    """The same reference re-pointed at the document that DECLARES what it names, with
    the ``description`` the chain passed through -- or ``None`` where its own target
    declares it.

    **HERE and not in ``codegen/emit.py``, which is §11's rule and
    ``adcp-client-python-10l.109``'s correction.**  This is a fact about the bundle's
    reference GRAPH -- an :class:`Edge` in and an :class:`Edge` out -- and §4 gives this
    module "every file read and every fact derived from a document".  It was written in
    ``emit.py``, where it read ``node["$ref"]`` and ``node.get("description")`` off a raw
    mapping; ``tests/test_import_rule.py``'s ``MAY_READ_A_DECLARATION`` reported it, and
    that set's own note carries the precedent verbatim: "``codegen/emit.py`` is NOT in
    this set and §14 step 7 is what removed it.  It held ``_composed_nodes``, the pointers
    a document's root ``allOf`` NAMES -- a fact about the bundle's reference GRAPH, which
    §11 puts in the source layer.  It is ``bundle.composed`` now."  Same shape, same
    answer, and the move is the whole of the change: not a line of the walk below differs.

    §5's ``$ref`` row reads "a fragment of another document → an import of a symbol the
    target declares", and the node a fragment names may be ITSELF a ``$ref``: then the
    target module IMPORTS that symbol and declares nothing at the pointer, so the row's
    sentence names no symbol at that site and the chain has to be walked to the module
    the sentence is about.  Binding the target's own imported name instead would be a
    re-export and §1's second way to reach one class; following the chain is one import
    path per class, from the declarer.

    **This is the reading the refusal at the one live site deferred** -- "10 of the 76
    [named nodes], in 3 documents, all 3 refused on a keyword of their own -- so 0 are
    reachable and the step whose population reaches one decides whether the chain is
    followed".  ``core/catalog-selection.json`` at ``/properties/type`` is that
    population arriving: its target ``core/catalog.json#/properties/type`` is a bare
    ``$ref`` to ``enums/catalog-type.json``, whose module declares ``CatalogType``.

    A hop is taken only where the node is a ``$ref`` naming a DOCUMENT of this bundle: a
    LOCAL pointer is one the target's own module resolves and declares, so there is
    nothing to follow, and a URI naming no document of the bundle is the refusal
    ``emit.answer``'s own screen already makes.  ``seen`` bounds the walk, so a chain that
    cycles between documents stops rather than recurring -- the caller then reports the
    site it stopped at, which is the refusal this function declined to replace.

    **The DESCRIPTION the chain passed through travels with it.**  A node the chain hops
    over may state a ``description`` sibling, and §5's ``$ref`` row gives a sibling the
    other answer -- "the sibling's description wins" -- while :func:`record` inlines
    exactly that text at the REFERRING pointer.  So a chain that returned only the symbol
    would leave the class stating nothing at a pointer the record states a sentence at,
    for a sentence the document itself wrote.  The FIRST sibling along the chain is the
    one taken, which is the record's own precedence: the referrer's own wins over it (read
    where the field is built) and it wins over the declarer's.

    ``None`` and not the edge unchanged, so a caller cannot recurse on its own input:
    the only edge this returns is one naming a DIFFERENT (document, pointer) site.
    """
    target, into, uri = edge.target, edge.into, edge.uri
    if target is None:
        # A LOCAL reference names no other document (:attr:`Edge.target`), so there is no
        # chain to follow and nothing to re-point at.  **Behaviour-preserving and not a new
        # screen**: in ``emit.py`` this fell through to ``read(bundle_dir, None)``, whose
        # ``TypeError`` the ``except`` below turned into the same ``None`` -- so the only
        # thing that changes is that the type checker can see it (the one mypy error the
        # move carried with the code).
        return None
    described: str | None = None
    seen = {(target, into)}
    while into:
        try:
            node = node_at(read(bundle_dir, target), into)
        except (KeyError, IndexError, TypeError, ValueError):
            return None
        if not isinstance(node, dict) or "$ref" not in node:
            break
        head, pointer = split_ref(str(node["$ref"]))
        if not head:
            break
        nxt = document_for(head, known)
        if nxt is None or (nxt, pointer) in seen:
            break
        text = node.get("description")
        if described is None and isinstance(text, str) and text:
            described = text
        seen.add((nxt, pointer))
        target, into, uri = nxt, pointer, str(node["$ref"])
    if (target, into) == (edge.target, edge.into):
        return None
    return edge._replace(target=target, into=into, uri=uri), described


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
    ISOLATION that branch admits a non-object, which is what ``lower.objects.lower_object``
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


def reported_drops(doc: object) -> tuple[tuple[str, str], ...]:
    """Every ``(pointer, keyword)`` this document states a REPORTED drop at.

    ``docs/plan/rebuild-plan.md`` §7's position rule: "**the drop is reported at every
    position the keyword occupies, and not only where a conjunct encloses it** [...] a
    keyword's effect is a decision about the keyword at a position; a report that reaches
    one position and not another is a defect in the CHANNEL, not a second decision."

    **This is that channel, and it cannot screen a position.**  The defect it replaces
    was ``lower.composition.lower_composition``'s conjunct worklist, which saw CONJ and nothing
    else: ``media-buy/sync-catalogs-request.json`` states ``errorMessage`` twice, at
    ``/allOf/1`` under a ``not`` and at ``/then`` beside a ``required``, and the reader
    was told about the first alone -- the second reached no reader at all, because
    ``lower.rules`` reads a ``then``'s ``required`` and its ``not`` and never asks the
    table about the rest of it.

    A function of the DOCUMENT alone, like every other derived fact in this module, over
    :func:`nodes_at` -- the one walk, which CARRIES the position the descent column
    assigned rather than recovering it from a pointer segment.  So the keyword is asked
    about at its own position and the answer is :attr:`keywords.Cell.reported`; what
    makes the report reach every position is that no arm here chooses one.

    The ROOT's pointer is ``""`` and the caller spells it ``"/"``, which is the line
    shape :attr:`compiler.Module.carries_nothing` states; the pointer is left as the walk
    produced it so that this stays a census and the prose stays the compiler's.
    """
    return tuple(
        (pointer, key)
        for pointer, node, position in nodes_at(doc)
        for key in sorted(node)
        if (answer := keywords.cell(key, position)) is not None and answer.reported
    )


def is_an_annotation(key: str, position: keywords.Position) -> bool:
    """Does this sibling of a ``$ref`` state nothing about ACCEPTANCE?

    The one question :func:`record` asks of a sibling, and the answer decides which
    side wins where the referring node and its target both state the key.  Read off
    the TABLE's effect column rather than from a set of annotation names, which §11
    names as one of today's repetitions: an annotation is a key whose cell compiles to
    no type, no field and no rule, which is what "states nothing about acceptance"
    IS.  A key in the ``x-`` namespace with no row of its own is one too -- §6 admits
    it by prefix -- and a key with no row and no prefix is not: the screen refuses the
    document on it, and until then the target's value is the one the draft holds.

    **The second clause went with ``Effect.REFUSE``** (§14 step 8): a REFUSE cell was
    excluded here because the document was about to be refused on it, so "whose value
    wins" was a question with no reader.  No cell can refuse, so the predicate is the
    effect column alone -- which is the sentence above, with nothing beside it.
    """
    answer = keywords.cell(key, position)
    if answer is None:
        return keywords.admitted_by_prefix(key)
    return answer.effect not in keywords.COMPILES


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
    wins = {k: v for k, v in siblings.items() if k not in placed or is_an_annotation(k, position)}
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


#: The walk's starting point, as a module-level singleton rather than a call in a
#: parameter default.  ``_Where`` is a ``NamedTuple``, so one instance is shared with no
#: risk a mutable default carries -- but a default that is a CALL is evaluated once at
#: import whatever its type, which is a fact about the shape and not about this class, and
#: a reader of the signature cannot tell the two apart.  Named here so the signature reads
#: a value.
_NOWHERE = _Where((), ())


class _Reached(NamedTuple):
    """One inlined node, beside WHAT THE TWO CYCLE GUARDS WERE CONSULTED FOR under it.

    **This is what makes :func:`record`'s share sound, and it is the whole of the
    argument.**  An inlined node is a function of the node, the document it is being
    copied out of, the position it is placed at -- and of :class:`_Where`, because the
    guards decide whether a reference under it refuses.  So a result computed under one
    :class:`_Where` may be handed to an occurrence standing at another ONLY where no
    guard consulted under it can answer differently there.

    The guards are consulted for exactly two things: a cross-document hop asks whether
    the document it is entering is in :attr:`_Where.chain`, and a local hop asks whether
    the ``(document, pointer)`` it is opening is in :attr:`_Where.anchors`.  So these are
    the two sets of what was ASKED -- every document entered under this node, and every
    local reference opened under it inside the same root scope -- and a held result is
    reusable at an occurrence whose own guards are DISJOINT from both.  Where they are
    not, the question the guard asks has a different answer and the node is inlined
    again.

    Each is the union of its children's, with the hop's own answer added as the hop is
    taken: a cross-document hop contributes the document it enters and RESETS the anchors,
    because :class:`_Where` resets them there -- a local reference opened below a copy
    cannot collide with one open above it.
    """

    #: The inlined node itself, which is what the caller places.
    node: dict
    #: Every document entered by a cross-document hop under this node.
    documents: frozenset[str]
    #: Every ``(document, pointer)`` a local hop opened under this node, inside the root
    #: scope this node is being copied out of.
    anchors: frozenset[tuple[str, str]]


def source_identities(bundle_dir: Path) -> dict[str, str]:
    """Per portable document, the digest of the BUNDLE TEXT its record is built from:
    its own raw bytes and the raw bytes of every document it transitively references.

    **The static half of :func:`record`, and it is here so the two can be told apart.**
    ``record`` is OUR RENDERING of a document -- it inlines, and what it inlines where
    is this package's decision, so its bytes move whenever that decision does.  This is
    the same document's UPSTREAM identity: nothing of the inliner reaches it, so it moves
    only when the bundle does.  A reader who needs "is this the same document" asks here,
    and a reader who needs "what does the self-contained form say" asks ``record``.

    **The one caller that needs the distinction is the held accepts corpus.**
    ``harness.corpus_key`` is the content address of the instances a pair's draw
    produced, and keyed on the rendering it misses every entry whenever the inliner
    changes -- for the share of the bundle whose record differs from its raw document at
    all, which is read by comparing ``record(bundle_dir, d)`` against
    ``read(bundle_dir, d)`` over :func:`portable` and is most of it.  The schema is
    static; the rendering is not; the key belongs on the static fact.  What makes that
    safe rather than looser is ``harness.corpus_defect``, which re-offers every held
    instance to the document on every read.

    **THE CLOSURE IS IN THE DIGEST, which is what the record's self-containment used to
    buy.**  Hashing the inlined record covered a dependency BY CONSTRUCTION -- the
    dependency's text is literally inside the dependent -- and dropping to the raw
    document alone would lose that: an upstream edit to a referenced document would leave
    the referrer's own bytes untouched and its key would hit.  So the closure is taken
    here instead, over :func:`edges` -- the reference graph read off the RAW mappings by
    the descent column -- and the member documents' bytes are hashed with it.  That is
    the same answer from the same upstream facts, and it is still not an edge list
    anybody maintains: the graph is derived from the ``$ref`` strings the documents
    themselves write.

    A member contributes its bundle-relative NAME, its length and its bytes, so no two
    different closures can agree by a concatenation accident and no absolute path enters
    the digest -- which is what keeps a key computed in one checkout equal to the same
    key computed in another (``tests/corpus.py``'s shared store).

    A reference naming no document of this bundle contributes nothing, exactly as
    ``emit.closure`` treats one: the site refuses where the pointer that carried it is,
    and a refusing document has no instances to hold.
    """
    documents = sorted(portable(bundle_dir))
    text = {d: (bundle_dir / d).read_bytes() for d in documents}
    targets: dict[str, set[str]] = {d: set() for d in documents}
    for edge in edges(bundle_dir):
        if edge.target is not None:
            targets[edge.document].add(edge.target)
    out: dict[str, str] = {}
    for document in documents:
        reached: set[str] = set()
        unread = [document]
        while unread:
            one = unread.pop()
            if one in reached:
                continue
            reached.add(one)
            unread += [t for t in targets.get(one, ()) if t not in reached]
        digest = hashlib.sha256()
        for member in sorted(reached):
            digest.update(f"{member}\0{len(text[member])}\0".encode())
            digest.update(text[member])
        out[document] = digest.hexdigest()
    return out


#: **A node of a record, keyed BY IDENTITY, to the site that STATES it**: ``id(node) ->
#: (stating document, stating pointer)``.
#:
#: ``docs/plan/rebuild-plan.md`` §8, "THE IDENTITY IS READ OFF THE NODE WHOSE KEYWORD THE
#: FACT IS" (decided 2026-11-03): "the inliner must export the origin of a node by
#: identity rather than by pointer: the walk folds a conjunct into the enclosing node's
#: pointer space, so a declared pointer is routinely at no pointer the record spells, and a
#: pointer-keyed origin map cannot answer."
#:
#: **BY IDENTITY and not by pointer, which is the whole of why this type exists.**  §8's
#: identity for an approximation is ``(stating document, stating pointer, keyword)`` and
#: "every inlined occurrence resolves to it" -- so a reader standing at an occurrence in
#: one record has to get back to the site the fact is STATED at.  A record pointer cannot
#: answer that: the record inlines a target at the REFERRING pointer, so one stating site
#: has as many record pointers as there are paths through the reference graph that reach
#: it, and the map in the other direction is not a function.  A node's identity is, because
#: :func:`record` places ONE OBJECT at every occurrence of one target (its own docstring's
#: "THE SAME OBJECT IS PLACED AT EVERY OCCURRENCE") -- so the occurrences of one stating
#: site are literally one object, and this maps that object to the site.
#:
#: Sound only while the record it was built for is alive, exactly as the ``by_id`` digest
#: map inside :func:`stored` is: ``id`` is reused once an object is freed.  So it travels
#: WITH the record as one value (:func:`recorded`) and never on its own.
Origins = dict[int, tuple[str, str]]


def record(bundle_dir: Path, document: str, known: Collection[str]) -> dict | Refusal:
    """:func:`recorded`'s FIRST HALF, which is what almost every reader wants.

    Kept as its own name because the map :func:`recorded` returns beside the record is
    only sound while that record is alive (:data:`Origins`) and because threading a value
    nobody opens through every reader would make one reader's cost everybody's: a
    whole-set emit reads a record 1,744 times and opens the origin map at one of them.
    """
    answer = recorded(bundle_dir, document, known)
    return answer if isinstance(answer, Refusal) else answer[0]


def recorded(
    bundle_dir: Path, document: str, known: Collection[str]
) -> tuple[dict, Origins] | Refusal:
    """THE DOCUMENT OF RECORD: ``document`` with every cross-document ``$ref`` inlined,
    and beside it :data:`Origins` -- the site that STATES each of its nodes, by identity.

    **The two are ONE value**, for :data:`Origins`' reason: an ``id``-keyed map is sound
    only while the objects it keys on are alive, so a caller that got the record from one
    call and the map from another would hold a map keyed on a record it threw away.

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
      in it, and every check it runs -- the draw, the document's own verdict on what it
      drew, the verdict on the dump -- reads THIS document rather than any
      canonicalisation of it.

    **``known`` IS AN ARGUMENT, and ``docs/plan/architecture.md`` is what makes it one:**
    "a callee that needs the set of a bundle's documents -- to resolve a reference's head
    against the documents that exist -- must be **told** it, not go and find it.  Finding
    it is a directory scan, and a callee reached once per node performs that scan once per
    node."  That is this function exactly: the set is read at ONE place below --
    :func:`document_for`, resolving the document half of a cross-document ``$ref`` -- and
    nothing else here consults it.  It was ``set(portable(bundle_dir))`` on entry, which is
    an ``rglob`` of the bundle and a sort of its paths, and the whole-set emit calls this
    1,744 times: **118.8 s of the run's 144.8 s of CPU was that one line**, measured off a
    counter in the run.

    **And not a cache, for the reason that section gives rather than as a style
    preference:** "a cache keyed on the directory path is wrong the moment a test builds a
    bundle in ``tmp_path`` and adds a document between calls; a cache keyed on the
    directory's contents has to read the contents, which is the cost.  So the set is
    computed once per run, by the caller that knows the run, and threaded to every reader
    that needs it."  A test building a bundle in ``tmp_path`` gets whatever it passes, by
    construction, and there is nothing to invalidate.

    It is REQUIRED and has no default, which is the whole of what the signature buys: a
    default of :func:`portable` would leave the scan one forgotten argument away and would
    make the cost invisible again at the next call site written.  :func:`declaring_site` is
    the precedent beside it -- same set, same name, same reason.

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

    **THE SAME OBJECT IS PLACED AT EVERY OCCURRENCE OF ONE TARGET, which costs no byte
    of the record and is what makes it buildable.**  ``json.dumps`` writes a shared
    object out once per occurrence, so the text is the text a fresh copy per occurrence
    wrote -- and §4's deep copy was never about the bytes.  It was about ALIASING, which
    is the reason stated at :func:`rebuilt`: "a record that aliased the bundle's own
    object would let one reader's edit reach another's".  That reason is answered by the
    readers rather than by a copy, and it was measured: the ONE reader that edits a
    record subtree is ``dump_exemptions.struck``, which deep-copies before it strikes and
    says so; ``harness.resolve`` deep-copies before it hands a document to a library
    that mutates; every other reader of a record -- ``undecidable_references`` here,
    ``json.dumps`` in ``emit``, ``applied_schema`` and ``schema_at`` in the package --
    reads, and ``applied_schema`` already returns the node it was given as the same
    object wherever nothing is conjoined.

    So a target is inlined ONCE per ``(node, the document it is copied out of, whether
    that document is this record's own, the position it is placed at)`` and the result is
    shared.  :class:`_Reached` is what keeps the share sound against the two cycle
    guards; its docstring is the argument and :func:`_beside` is why the position is in
    the key.  The referring node's own keys are NOT in it: ``_beside`` builds a fresh
    mapping per occurrence out of the shared one, so two occurrences of one target with
    different siblings get different nodes and share everything below them.

    MEASURED on the 3.2 bundle, which is why this is here: 5,363,667 bytes of bundle
    source became 365,030,691 bytes of record, and ``core/mcp-webhook-payload.json``'s
    957,187 nodes were 6,442 distinct ones -- one subtree placed 1,957 times.  The record
    is a TREE where the document is a DAG, and the duplication was in the BUILD as well
    as in the text.  The text is unchanged here and stays 44 MB; what this removes is
    re-walking and re-copying one target once per path that reaches it.
    """
    roots: dict[str, dict] = {document: read(bundle_dir, document)}
    #: The inlined target per key, held for the life of this call.  ``id(node)`` is the
    #: node's identity and is stable because ``roots`` holds every document alive: every
    #: node this descent is handed is a node of a parsed document, never one it built.
    shared: dict[tuple[int, str, bool, keywords.Position], _Reached] = {}
    #: :data:`Origins`, filled as each node of the record is BUILT -- which is the one
    #: place that knows both halves: ``home`` is the document whose text the node is and
    #: ``stated`` is its pointer inside that document.  A node this descent builds is
    #: alive for as long as the record is, so the keys stay the keys of these nodes.
    origins: Origins = {}

    def root_of(name: str) -> dict:
        if name not in roots:
            roots[name] = read(bundle_dir, name)
        return roots[name]

    def refuse(pointer: str, detail: str) -> Refusal:
        return Refusal("$ref", pointer, detail, kind=Kind.VERDICT)

    def placed(
        uri: str,
        *,
        pointer: str,
        home: str,
        scope: dict | None,
        where: _Where,
        position: keywords.Position,
    ) -> _Reached | Refusal | None:
        """The node a reference names, inlined and ready to be placed, or ``None`` where
        the reference STAYS as written.

        ``None`` is the one case §4 leaves alone: a LOCAL reference of the document whose
        record this is, which ``scope is None`` says we are at.

        The hop's own guard answer is added to what :class:`_Reached` carries up: the
        document a cross-document hop ENTERS, and the ``(document, pointer)`` a local hop
        OPENS.  A cross-document hop resets the anchors it carries up for the reason
        :class:`_Where` resets them -- a local reference opened inside a copy is not open
        outside it.
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
            crossed, opened = False, frozenset({(home, into)})
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
            crossed, opened = True, frozenset()
        try:
            target = node_at(root, into)
        except (KeyError, IndexError, TypeError, ValueError):
            return refuse(pointer, f"{uri} names no node of {at_home}")
        if not isinstance(target, dict):
            return refuse(
                pointer, f"{uri} names a {type(target).__name__} of {at_home}, not a schema"
            )
        # ``stated=into``: the target's own pointer is its pointer in the document being
        # copied out of, which is exactly what the reference's fragment names.  THIS is
        # where the record's pointer space and the stating document's part company -- the
        # answer is placed at ``pointer``, the REFERRING pointer, and states what it
        # states at ``into`` in ``at_home``.
        answer = inline(
            target,
            pointer=pointer,
            home=at_home,
            scope=root,
            where=where,
            position=position,
            stated=into,
        )
        if isinstance(answer, Refusal):
            return answer
        # A CROSS-DOCUMENT hop carries up NO anchor of the copy it took, because every
        # one of them was opened inside a root scope this hop stands outside of -- which
        # is the same fact ``where`` states by resetting them.
        return _Reached(
            answer.node,
            answer.documents | ({at_home} if crossed else frozenset()),
            opened if crossed else (answer.anchors | opened),
        )

    def inline(
        node: dict,
        *,
        pointer: str,
        home: str,
        scope: dict | None,
        position: keywords.Position = keywords.Position.ROOT,
        where: _Where = _NOWHERE,
        stated: str = "",
    ) -> _Reached | Refusal:
        """``node`` with every reference under it inlined, or the first refusal reached.

        ``home`` is the document whose text this node is and ``scope`` is the root a
        local pointer in it resolves against -- ``None`` at the document whose record
        this is, where a local reference is left as written.  ``where`` carries the two
        cycle guards.  ``stated`` is this node's own pointer INSIDE ``home``, which is
        what :data:`Origins` records and is NOT ``pointer``: ``pointer`` is where the
        answer is placed in the record being built, and the two part company at every
        reference the record resolves by copying.

        **``stated`` is not in the key and does not have to be**, because it is a
        FUNCTION of the key's first two components: a node object sits at exactly one
        pointer of the document its text is, so ``(id(node), home)`` determines it.  A
        held answer therefore carries the same origin the recomputed one would.

        **Computed once per key and shared**, which is the docstring above.  The key is
        everything the ANSWER is a function of other than the guards -- the node's
        identity, the document it is being copied out of, whether that document is this
        record's own (``scope is None``, which decides whether a local reference is
        followed at all), and the position, which :func:`_beside` reads.  The guards are
        answered by :class:`_Reached` instead of being keyed on: a held answer is reused
        where nothing it consulted them for can answer differently at this occurrence,
        and inlined again where something can -- which is a reference cycle, and leaves
        the record undefined one hop further down.

        ``pointer`` is not in the key and must not be: it names WHERE a refusal is, and
        no refusal is held.  So a refused reference is reported at the pointer that
        carried it, once per occurrence, exactly as it was before this shared.
        """
        at = (id(node), home, scope is None, position)
        held = shared.get(at)
        if (
            held is not None
            and held.documents.isdisjoint(where.chain)
            and held.anchors.isdisjoint(where.anchors)
        ):
            return held
        answer = inlined(
            node,
            pointer=pointer,
            home=home,
            scope=scope,
            position=position,
            where=where,
            stated=stated,
        )
        # Held only where nothing was: an answer computed because a held one was unusable
        # is this occurrence's and narrower, and the unusable one is still the answer for
        # every occurrence that can use it.  A REFUSAL is never held, because it names the
        # pointer that carried the reference.
        if held is None and not isinstance(answer, Refusal):
            shared[at] = answer
        return answer

    def inlined(
        node: dict,
        *,
        pointer: str,
        home: str,
        scope: dict | None,
        position: keywords.Position,
        where: _Where,
        stated: str,
    ) -> _Reached | Refusal:
        """``node``'s inlining computed from nothing held.  :func:`inline` is the share.

        Every node this builds is recorded in :data:`Origins` at ``(home, stated)``,
        which is the site the DOCUMENT states it -- the one reading §8's identity needs
        and the one no pointer of the record being built can give.
        """
        uri = node.get("$ref")
        if isinstance(uri, str):
            copied = placed(
                uri,
                pointer=pointer,
                home=home,
                scope=scope,
                where=where,
                position=position,
            )
            if isinstance(copied, Refusal):
                return copied
            if copied is not None:
                # ``_beside`` is per OCCURRENCE: the referring node's own keys are not in
                # the key, and the mapping it builds is fresh around the shared one.
                #
                # **ITS ORIGIN IS THE TARGET'S AND NOT THE REFERRER'S**, which is §8's
                # "THE IDENTITY IS READ OFF THE NODE WHOSE KEYWORD THE FACT IS."  The
                # referring node states a ``$ref`` and annotations; every keyword that
                # says anything about an instance here is the TARGET's, because draft-07
                # ignores a constraining sibling of a ``$ref`` and :func:`_beside` keeps
                # the target's value where both state one.  So a fact read off this node
                # is a fact the TARGET's document states, and that is the site it
                # resolves to -- the referrer's own pointer would make one stating site
                # own as many identities as it has referrers, which is the counting §8
                # forbids.
                beside = _beside(copied.node, node, position)
                site = origins.get(id(copied.node))
                if site is not None:
                    origins[id(beside)] = site
                return _Reached(beside, copied.documents, copied.anchors)
        done: dict[str, object] = {}
        documents: frozenset[str] = frozenset()
        anchors: frozenset[tuple[str, str]] = frozenset()
        for _, suffix, sub, holds in subschemas(node):
            if not isinstance(sub, dict):
                continue  # not a schema; §3 drops nothing, so ``rebuilt`` keeps it
            answer = inline(
                sub,
                pointer=f"{pointer}{suffix}",
                home=home,
                scope=scope,
                position=holds,
                where=where,
                stated=f"{stated}{suffix}",
            )
            if isinstance(answer, Refusal):
                return answer
            done[suffix] = answer.node
            documents |= answer.documents
            anchors |= answer.anchors
        built = {
            key: rebuilt(key, value, done) if key in DESCENDS else value
            for key, value in node.items()
        }
        origins[id(built)] = (home, stated)
        return _Reached(built, documents, anchors)

    answer = inline(
        roots[document],
        pointer="",
        home=document,
        scope=None,
        where=_Where((document,), ()),
        stated="",
    )
    if isinstance(answer, Refusal):
        return answer
    return stored(answer.node, origins), origins


def rebuilt(
    keyword: str,
    held: object,
    done: Mapping[str, object],
    *,
    missing: Callable[[object], object] = copy.deepcopy,
) -> object:
    """``held`` with each subschema replaced by the one its caller computed for it.

    The inverse of :func:`subschemas` for one keyword, and BOTH descents that rebuild a
    document need exactly it: :func:`record` places an inlined copy and
    :func:`codegen.patch.rewritten` places a ``$ref`` where a copy stood.  Two spellings
    of "put the subschema back where it came from" is how an inliner and a patcher come
    to disagree about which node a pointer names.

    It rebuilds the keyword's own SPELLING: a map stays a map with its keys in their own
    order, a list stays a list of the same length, one schema stays one.  A value the descent did not reach -- an
    ``additionalProperties: false``, an ``items`` that is neither a schema nor a list of
    them -- is deep-copied as it stands, because §3 drops nothing and because a record
    that aliased the bundle's own object would let one reader's edit reach another's.
    ``missing`` is what a value the descent did not reach becomes, and it DEFAULTS to the
    deep copy the paragraph above argues for.  :func:`stored` passes the identity instead,
    because what it builds out of this is hashed and thrown away: a copy there would walk
    every ``enum`` of every node of the record to answer a question about the node's own
    text.  Both readers that PLACE a subschema take the default.
    """

    def done_or_missing(suffix: str, sub: object) -> object:
        return done[suffix] if suffix in done else missing(sub)

    if keyword in HELD_BY_NAME and isinstance(held, dict):
        return {
            key: done_or_missing(f"/{keyword}/{escape_key(key)}", sub)
            for key, sub in held.items()
        }
    if isinstance(held, list):
        return [done_or_missing(f"/{keyword}/{i}", sub) for i, sub in enumerate(held)]
    if isinstance(held, dict):
        return done_or_missing(f"/{keyword}", held)
    return missing(held)


def _itself(value: object) -> object:
    """``value``, uncopied: :func:`rebuilt`'s ``missing`` for a reader that only HASHES.

    Named rather than written as a lambda at the call site because the argument it is
    passed as carries a decision -- :func:`rebuilt`'s docstring says which -- and a lambda
    there says only "do nothing" without saying what that is safe for.
    """
    return value


def stored(record: dict, origins: Origins | None = None) -> dict:
    """``record`` STATING EACH DISTINCT SUBTREE ONCE, under its own ``definitions``.

    ``origins`` is :data:`Origins` over ``record``'s OWN nodes, re-keyed IN PLACE onto the
    nodes this builds -- which is §8's "carried across the storage rebuild".  It has to be
    in place and it has to be here: every node of the answer is a fresh object, so a map
    keyed on the input's identities answers nothing about the output, and the input's nodes
    are freed the moment this returns, which would make those keys reusable by somebody
    else's objects.  ``None`` for a caller that wants only the storage.

    **An interned content takes the origin of the node the intern CHOSE**, which is the
    representative :func:`digest` saw first.  Two stating sites whose text is identical are
    one subtree in the record -- that is what "states each distinct subtree once" means --
    so they are one object and can carry one origin; the one chosen is the one the
    document first reaches, by the same walk that names the entries.

    ``docs/plan/architecture.md``, "THE RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT":
    "The record stores each distinct subtree once under its own ``definitions`` with a
    local reference at each occurrence.  **Every pointer any reader SPELLS keeps the
    spelling it has today.**  The hoisting is a storage representation and the readers
    dereference through it; it is not a renaming."

    So this changes WHAT A RECORD STATES NOT AT ALL and only how it is stored.  A node at
    a schema position whose content occurs more than once is written once under
    :data:`adcp.types._base.STORE_SECTION` and replaced, at each occurrence, by the local
    reference naming it -- draft-07 resolves that reference against the document root,
    which is the document the package carries beside the module, so the payload a document
    admitted before it admits after and ``strict_validate`` resolves the reference against
    the referrer exactly as it already resolves a document's own.

    **The whole node is replaced and no sibling is left beside the reference**, which is
    what makes the replacement an identity rather than a reading of draft-07's
    sibling rule.  Draft-07 IGNORES every key beside a ``$ref``, so a reference written
    with siblings would state the target alone and the siblings would be text nothing
    reads; the occurrence's own keys are PART of the content hashed, so two occurrences
    differing in a ``description`` are two contents and share nothing.

    **WHY IT IS NEEDED, measured** (``adcp-client-python-82m.25``): the bundle's 1,054
    portable documents are 5,363,667 bytes of source and their inlined records were
    835,864,437 bytes committed, with ``core/mcp-webhook-payload.json`` alone at
    112,920,473 -- 957,187 nodes carrying 6,442 distinct ones, one subtree placed 1,957
    times.  The record was a TREE where the document is a DAG.  The duplication was never
    the bundle's: it is what inlining a reference graph structurally produces.

    **WHICH SUBTREES, and the rule is IN-DEGREE over the consed graph rather than
    occurrences in the text.**  Content is interned, every distinct content's own child
    edges are counted, and a content with two or more in-edges is stored.  That is
    exactly "each distinct subtree once": a content with ONE in-edge has one parent, and
    walking up from it reaches a stored ancestor or the root along one path, so its text
    appears once whether it is stored or not -- while a content with two reaches two.
    Counting occurrences in the expanded text instead would ask a question about 957,187
    nodes to decide 6,442.

    Two nodes are never stored, each for a reason that is not a threshold:

    * the ROOT, which cannot arise -- a finite acyclic record's root content cannot occur
      strictly inside itself, so the root's in-degree is 0 -- and which is written as the
      exclusion it is, because the root is where the section itself is added;
    * a node that IS already a bare reference.  Storing one writes a reference to a
      reference, which is longer than the node it replaces and buys nothing.

    **THE ENTRY NAMES ARE ASSIGNED IN A WALK OF THE CONSED GRAPH** and not in hash order,
    so the name a subtree gets is a function of where the document first reaches it.  The
    emission is byte-stable under that: the record is dumped with its keys sorted, so the
    one thing a node's own key order could move -- which object of an interned content is
    the representative -- reaches no byte.

    **A COLLIDING ENTRY IS A BUILD FAILURE**, which is §2's rule for a property of the
    compiler rather than of a document: the predicate the package dereferences through
    (:func:`adcp.types._base.through_the_store`) reads the entry's NAME, so a document
    already holding one would make the storage indistinguishable from its own text and the
    two would resolve to different nodes.  Measured over the 3.2 bundle: 0 entries under
    the prefix in any document, raw or recorded.
    """
    #: The content digest per node OBJECT.  Keyed on ``id`` because the record already
    #: shares one object per inlined target (:func:`record`), so this is one digest per
    #: distinct object rather than one per occurrence; ``record`` holds every one of them
    #: alive for the length of this call.
    by_id: dict[int, str] = {}
    #: Per distinct CONTENT: one node that has it, and the suffix -> content of its own
    #: child subschemas.  The graph this function reasons over is this mapping.
    body: dict[str, dict] = {}
    edges: dict[str, dict[str, str]] = {}
    #: In-edges per content, counted once per edge of the consed graph above.
    into: dict[str, int] = {}

    def digest(node: dict) -> str:
        held = by_id.get(id(node))
        if held is not None:
            return held
        children = {
            suffix: digest(sub)
            for _, suffix, sub, _ in subschemas(node)
            if isinstance(sub, dict)
        }
        # The node's own text with each child subschema standing as its digest, which is
        # what makes the hash a function of the whole subtree while costing the node's own
        # size.  ``_itself`` because this mapping is serialised and dropped.
        canonical = {
            key: rebuilt(key, value, children, missing=_itself) if key in DESCENDS else value
            for key, value in node.items()
        }
        at = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, default=str).encode()
        ).hexdigest()
        by_id[id(node)] = at
        if at not in body:
            body[at] = node
            edges[at] = children
            for child in children.values():
                into[child] = into.get(child, 0) + 1
        return at

    root = digest(record)
    names: dict[str, str] = {}

    def is_stored(at: str) -> bool:
        """Whether the content ``at`` is written once under the section, which is the
        in-degree rule and the two exclusions the docstring argues."""
        if at == root or into.get(at, 0) < 2:
            return False
        node = body[at]
        return not (len(node) == 1 and "$ref" in node)

    #: Breadth-first over the consed graph from the root, children in the node's own key
    #: order, so an entry's name says where the document first reaches the subtree.
    unread = [root]
    reached = {root}
    while unread:
        one = unread.pop(0)
        if is_stored(one):
            names[one] = _base.store_entry(len(names))
        for child in edges[one].values():
            if child not in reached:
                reached.add(child)
                unread.append(child)

    built: dict[str, dict] = {}
    #: :data:`Origins` re-keyed onto the nodes :func:`build` makes, written as they are
    #: made and copied back over ``origins`` at the end.  Separate from ``origins`` while
    #: the build runs because the input's keys are still being READ: an ``id`` the build
    #: happens to reuse would otherwise overwrite an entry a later node still needs.
    carried: Origins = {}

    def build(at: str) -> dict:
        held = built.get(at)
        if held is not None:
            return held
        node = body[at]

        def placed(child: str) -> dict:
            """The child as this record stores it: the entry's reference, or the node.

            **A STORED child's reference carries the ENTRY's origin**, because a reader
            resolving an occurrence to its stating site dereferences through the storage
            -- ``architecture.md``'s "a reader asking what the document states reads
            through the storage", which :func:`expanded` and
            ``adcp.types._base.through_the_store`` are the two existing spellings of.  So
            the reference object gets the site the entry states, and a reader that stops
            at the reference gets the same answer as one that follows it.  Keyed per
            OCCURRENCE: each reference is a fresh mapping, which is what lets one entry's
            many occurrences each carry it.
            """
            if child not in names:
                return build(child)
            ref = {"$ref": _base.store_ref(names[child])}
            if origins is not None:
                site = origins.get(id(body[child]))
                if site is not None:
                    carried[id(ref)] = site
            return ref

        done = {suffix: placed(child) for suffix, child in edges[at].items()}
        out = {
            key: rebuilt(key, value, done, missing=_itself) if key in DESCENDS else value
            for key, value in node.items()
        }
        built[at] = out
        if origins is not None:
            site = origins.get(id(node))
            if site is not None:
                carried[id(out)] = site
        return out

    def flush() -> None:
        """``carried`` over ``origins``, LAST, so every node this built is in it.

        After the section's entries, which :func:`build` makes too: a stored subtree is
        where the record keeps the node, and a reader resolving an occurrence to its
        stating site arrives at the entry rather than at the reference naming it.
        """
        if origins is not None:
            origins.clear()
            origins.update(carried)

    out = build(root)
    if not names:
        flush()
        return out
    section = out.get(_base.STORE_SECTION)
    section = dict(section) if isinstance(section, dict) else {}
    colliding = sorted(set(section) & set(names.values()))
    if colliding:
        raise BuildFailure(
            f"the record's own {_base.STORE_SECTION} section already holds "
            f"{colliding}, so a stored subtree cannot be told from the document's own "
            f"text: {_base.STORE_PREFIX!r} is the one prefix "
            "adcp.types._base.through_the_store dereferences through"
        )
    section.update((entry, build(at)) for at, entry in names.items())
    answer = {**out, _base.STORE_SECTION: section}
    # The ROOT is re-made here -- ``{**out, ...}`` is a fresh mapping -- so its own entry
    # is re-keyed onto the object the caller actually gets.  The root's stating site is
    # the document's own root, which is what ``recorded`` enters the descent at.
    site = carried.get(id(out))
    if site is not None:
        carried[id(answer)] = site
    flush()
    return answer


def expanded(node: object, root: object) -> object:
    """``node`` with the record's own STORAGE put back: :func:`stored`'s inverse.

    **The reading is :func:`adcp.types._base.store_expanded`'s and this is the name this
    module's own readers say.**  The package carries the record, so the package carries
    the dereference -- one declaration of what the storage is and how it is read, for the
    same reason :class:`adcp.types._base.SchemaRef` is declared there and not here.  A
    second walk in this module would be a second reading of one storage, and the two would
    come to disagree about which pointers resolve.

    The two callers are this package's own: ``harness.resolve``, which hands the payload
    generator a self-contained copy and must not hand it the storage -- the library's
    resolver merges a FRESH resolution at every reference and holds no memo, so delegating
    the storage to it hands back exactly the duplication the storage removed, measured at
    21.5 s against 323 s over ``adagents.json``'s 37 pairs -- and the tests that grade the
    round trip.
    """
    return _base.store_expanded(node, root)


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
      reference names it.

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


# --------------------------------------------------------------------------- #
# a DRIFTED FAMILY: the one envelope the bundle repeats and spells many ways
# --------------------------------------------------------------------------- #
# ``docs/plan/architecture.md`` §11 puts these here: this module "owns every file read
# and every fact derived from a document", and a family is a fact derived from every
# document of the bundle.  The predicates above are the precedent -- ``is_leaf_object``,
# ``references_a_property`` and ``carries_an_enum`` are shape predicates over a raw
# document -- and §4's rule that ``schema/parse.py`` is the one reader of a raw mapping
# is what keeps the derivation out of ``lower/``: a bundle-wide census cannot parse 1,054
# documents, and ``codegen/lower/envelope.py`` turns these facts into a declaration
# without holding a mapping.
#
# ``codegen/lower/envelope.py`` carries the whole of WHY the family earns a base; what is
# here is WHICH nodes are in it and WHAT they agree on.

#: **The family's defining statement, and the whole of its membership test.**  A node is a
#: member when it declares exactly these property keys and requires exactly this one.
#: Two facts and nothing else -- not a title, not a document path -- so membership is the
#: SHAPE at one node and a 27th envelope upstream joins by stating it.  A hand-written
#: list of member documents would be complete with respect to itself, which is the defect
#: ``docs/plan/rebuild-plan.md`` §4 rejects for branch discrimination: what it omits
#: passes in both directions and nothing says so.
ENVELOPE_PROPERTIES = frozenset({"context", "errors", "ext"})
ENVELOPE_REQUIRED = ("errors",)


class Envelope(NamedTuple):
    """One member of the family: the document that states it and the pointer it is at."""

    document: str
    pointer: str


class Agreed(NamedTuple):
    """What every member of the family states alike about one of its properties."""

    key: str
    required: bool
    #: The descent path from the property's own node to the agreed reference, as the
    #: POSITIONS the table's descent column assigned -- ``()`` where the property IS the
    #: reference.
    path: tuple[keywords.Position, ...]
    #: The bundle document every member reaches at the end of :attr:`path`.
    target: str


def is_an_envelope(node: object) -> bool:
    """**The membership test: the shape, never the name.**

    A predicate over ONE node and nothing else, so it answers the same way whatever else
    a run was named (``docs/plan/rebuild-plan.md`` §9), and the family is whatever states
    the shape.
    """
    if not isinstance(node, Mapping):
        return False
    properties = node.get("properties")
    if not isinstance(properties, Mapping) or frozenset(properties) != ENVELOPE_PROPERTIES:
        return False
    required = node.get("required")
    if not isinstance(required, list):
        return False
    return tuple(required) == ENVELOPE_REQUIRED


def envelopes(bundle_dir: Path) -> tuple[tuple[Envelope, dict], ...]:
    """Every member of the family, in document order, with the node that states it.

    A function of the BUNDLE and never of a run's document set, which is the property
    :func:`named` is written for and for the same reason: the base derived from this is
    the same text whichever documents a run was named, so a member's own module is too.
    Read off :func:`nodes`, the one walk, so a member is a node at a SCHEMA position and
    not a mapping that happens to hold the three keys.
    """
    return tuple(
        (Envelope(document, pointer), node)
        for document in portable(bundle_dir)
        for pointer, node in nodes(read(bundle_dir, document))
        if is_an_envelope(node)
    )


def _reaches(
    node: object, documents: Collection[str], path: tuple[keywords.Position, ...] = ()
) -> Iterator[tuple[tuple[keywords.Position, ...], str]]:
    """Every ``(descent path, target document)`` a subschema references a type from.

    Descends by :func:`subschemas` -- the one descent step -- so the path is the column's
    own answer and no position is recovered from a pointer string
    (``docs/plan/architecture.md`` §6).  A hop the column puts at RULE is not taken:
    ``docs/plan/rebuild-plan.md`` §3 lowers no type from a rule position and nothing below
    one is lowered either, so a reference there states no type a family could agree on --
    which is :func:`lowers_no_type`'s rule, read as the walk takes it rather than as a
    second pointer census.
    """
    if not isinstance(node, Mapping):
        return
    uri = node.get("$ref")
    if isinstance(uri, str):
        target = document_for(split_ref(uri)[0], documents)
        if target is not None:
            yield path, target
    for _, _, sub, position in subschemas(node):
        if position is keywords.Position.RULE:
            continue
        yield from _reaches(sub, documents, (*path, position))


def _agreed(key: str, stated: list[object], documents: Collection[str]) -> Agreed:
    """The shortest descent path at whose end every member reaches ONE document.

    A candidate is a ``(path, target)`` pair every member reaches THROUGH: the member
    states a reference to ``target`` at ``path`` or somewhere below it.  A member that
    descends further says MORE about the property than the family agrees on, and §2's
    ``allOf`` row makes saying more a SUBCLASS of what is said -- so the prefix is a
    supertype of every member's own answer rather than a claim about it.

    Only the MINIMAL candidates are kept, since an extension of a candidate every member
    reaches is covered by the candidate.  Two minimal candidates means the family reaches
    two unrelated types at one property and there is no agreed answer, which is a
    ``BuildFailure``: the compiler has met a bundle its rule does not cover, which is
    neither a document's outcome nor something to guess at.
    """
    reached = [frozenset(_reaches(one, documents)) for one in stated]
    candidates = {
        pair
        for pair in frozenset().union(*reached)
        if all(
            any(p[: len(pair[0])] == pair[0] and t == pair[1] for p, t in one)
            for one in reached
        )
    }
    minimal = {
        pair
        for pair in candidates
        if not any(
            other != pair and pair[0][: len(other[0])] == other[0] and pair[1] == other[1]
            for other in candidates
        )
    }
    if len(minimal) != 1:
        raise BuildFailure(
            f"the envelope family's {key!r} reaches {sorted(minimal) or 'no'} agreed "
            f"document over {len(stated)} members, and a base states one or none"
        )
    path, target = next(iter(minimal))
    return Agreed(key, key in ENVELOPE_REQUIRED, path, target)


def envelope_shape(
    members: Collection[tuple[Envelope, dict]], documents: Collection[str]
) -> tuple[Agreed, ...]:
    """What every member of the family states alike, one entry per property.

    The ORDER is the members' own and is itself an agreement: a family listing its keys in
    two orders has no one order for a base to declare, and declaring one anyway would
    reorder a member class's fields by a choice made here rather than by the documents.
    Measured over bundle 3.2: all 26 state ``errors``, ``context``, ``ext``.

    **A bundle stating no member has no family and the answer is empty**, which is not a
    defect and must not be one: the family is DERIVED, so a bundle that does not repeat
    the envelope simply earns no base, and every hand-built bundle a test hands this
    package is in that position.  A ``BuildFailure`` here would make the compiler refuse
    a bundle for not being 3.2, which is the opposite of deriving the set.
    """
    if not members:
        return ()
    orders = {tuple(node["properties"]) for _, node in members}
    if len(orders) != 1:
        raise BuildFailure(
            f"the envelope family states its properties in {len(orders)} orders "
            f"({sorted(orders)}), and a base declares one"
        )
    return tuple(
        _agreed(key, [node["properties"][key] for _, node in members], documents)
        for key in next(iter(orders))
    )
