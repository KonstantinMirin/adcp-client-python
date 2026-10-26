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

from codegen import compiler, keywords
from codegen.lower import rules, union
from codegen.refusal import Kind, Refusal

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
    (``compiler.escape_key``), and the position is the one the table says the keyword
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
                    yield keyword, f"/{keyword}/{compiler.escape_key(key)}", sub, position
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


def nodes(node: object, pointer: str = "") -> Iterator[tuple[str, dict]]:
    """Every ``(JSON Pointer, subschema)`` at a SCHEMA POSITION in the document.

    The one walk.  ``schema_keywords`` and ``references`` are both read off it, so
    the two censuses cannot come to disagree about what a schema position is --
    which is the same reason ``harness`` declares its descent tables beside both
    of its walks.  It descends by :func:`subschemas`, so the walk and
    :func:`record`'s inliner read one declaration of what a schema position is.
    """
    if isinstance(node, list):
        for i, v in enumerate(node):
            yield from nodes(v, f"{pointer}/{i}")
        return
    if not isinstance(node, dict):
        return
    yield pointer, node
    for _, suffix, sub, _ in subschemas(node):
        yield from nodes(sub, f"{pointer}{suffix}")


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
            target = compiler.node_at(root, into)
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
            key: done_or_copy(f"/{keyword}/{compiler.escape_key(key)}", sub)
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
        f"{pointer}/{kw}/{compiler.escape_key(key)}"
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
        for pointer, uri in references(resolved_doc)
        if split_ref(uri)[0] and reaches(pointer, entries=entries, declared=named)
    ]


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
