"""A PATCH SET, and the patched bundle applying one produces.

``docs/plan/rebuild-plan.md`` §1, "A patched bundle is a legitimate input, and the test
is the RECORD": the bundle handed to the compiler may be a patched copy of the published
one, and **a patch is admissible exactly when every patched document's record is
byte-identical to the published document's record.**  That is this module's whole reason
to exist in the SOURCE layer beside :mod:`codegen.bundle`: a patched bundle is an INPUT,
not a compiler decision, so nothing downstream of here learns that a patch was applied.

**What a patch set is.**  New documents, plus a manifest naming the node in each new
document that the sites come to reference.  It is not a forked bundle: the 1,054 published
documents stay where they are and the patch is the upstream diff, literally -- for #8525,
six files and a rewrite rule, reviewable in one sitting.

**MEASURED, and the measurement is this module's own finding.**  Byte-identity does NOT
hold for the extraction #8525 asks upstream for, and the reason is structural rather than a
defect in the patch: ``record`` inlines a reference's target WHOLE, so a site that comes to
reference a TITLED document also takes that document's ``title`` and ``$schema`` into the
record, where the published site had neither.  §1 asks for byte-identity in one sentence
and for a titled document in the next, and the two cannot both hold.  What DOES hold, over
all 1,054 documents, is the condition byte-identity was reached for: no keyword that
decides acceptance differs at any pointer (:func:`seen_by_a_validator`).  Both figures are
reported; which of the two is the admissibility line is the plan's call and not this
module's.

**The one rewrite.**  :func:`rewritten` replaces a subschema with a ``$ref`` to the node
the manifest names, and leaves every other key of that subschema where it was.  It is the
INVERSE of :func:`codegen.bundle.record`, which inlines a reference's target and keeps the
referring node's keys beside it, and the two descend and rebuild by the same pair of
functions (:func:`codegen.bundle.subschemas`, :func:`codegen.bundle.rebuilt`) so they
cannot disagree about which node a pointer names.

**Why the match is so narrow.**  A site is rewritten only when the manifest's node accounts
for every key of it that is not an ANNOTATION, and ``is_an_annotation`` is
:func:`codegen.bundle.record`'s own predicate rather than a list of key names.  Draft-07
IGNORES every sibling of a ``$ref``, so a CONSTRAINING key left beside one is a key the
patched document no longer asserts -- the record would still show it, because ``_beside``
keeps it, and the check would pass over a patch that had quietly widened the protocol.
Requiring the node to account for all of them closes that gap at the only place it can be
closed, which is the match.
"""

from __future__ import annotations

import copy
import json
import shutil
from collections.abc import Collection, Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

from codegen import bundle, keywords

#: The manifest's filename inside a patch set directory.
MANIFEST = "manifest.json"
#: The directory inside a patch set holding the new documents, laid out at the paths they
#: take in the bundle.
DOCUMENTS = "documents"


class Extraction(NamedTuple):
    """One repeated subschema, the document it moves into, and where the sites point.

    ``subschema`` is READ from the new document at ``pointer`` and is never written in the
    manifest, so the thing the sites must match and the thing they resolve to are one
    object.  A manifest that stated it separately would be a second copy of the patch, and
    a patch whose two copies drifted would pass the record check at the sites it still
    matched and silently skip the rest.

    ``apart`` is the one thing a walk cannot decide: a site whose SHAPE matches and whose
    MEANING does not.  ``^[A-Z]{3}$`` is a currency code at 83 sites and an IATA airport
    code at two, and a document named for one of those asserts, at the other, something
    the bundle never said.  So the exclusions are written down, each with the reason the
    reviewer needs, and :func:`load` refuses one that matches nothing -- a stale exclusion
    would silently widen the patch the day the site it named moved.
    """

    #: Bundle-relative path of the new document.
    document: str
    #: JSON Pointer into that document naming the node the sites reference; ``""`` is its
    #: root.
    pointer: str
    #: The ``$ref`` URI the sites are given, in the published bundle's own spelling.
    uri: str
    #: The node at ``pointer``.
    subschema: dict
    #: ``(document, pointer)`` of each shape-matching site that means something else.
    apart: frozenset[tuple[str, str]]


def base_uri(bundle_dir: Path) -> str:
    """The prefix the bundle's own absolute ``$ref``\\ s put before a document path.

    DERIVED from the published bundle rather than written down, for ``bundle.document_for``'s
    reason: every reference in 3.2 is spelled ``.../schemas/3.2.4/<path>``, and a literal
    here would be a version in ``codegen/`` (D9) and would be wrong for a bundle publishing
    under a different base.  Read off the references that already resolve: the prefix a URI
    has left once the document path it names is taken off its end.

    Raises ``ValueError`` where the bundle's absolute references disagree about the prefix
    or state none, because then there is no spelling a new reference could take that the
    bundle would recognise as its own.
    """
    documents = set(bundle.portable(bundle_dir))
    found = set()
    for edge in bundle.edges(bundle_dir):
        head, _ = bundle.split_ref(edge.uri)
        if not head:
            continue
        named = bundle.document_for(head, documents)
        if named is not None and head.endswith(named):
            found.add(head[: len(head) - len(named)])
    if len(found) != 1:
        raise ValueError(
            f"{bundle_dir}: its absolute references state {len(found)} distinct base URIs "
            f"({sorted(found)}), so a new reference has no spelling to take"
        )
    return found.pop()


def load(patch_set: Path, published: Path) -> tuple[Extraction, ...]:
    """The patch set's extractions, in manifest order, with each subschema read.

    Raises ``ValueError`` for a manifest entry naming a document the patch set does not
    carry, a pointer naming no node of it, or a document path the published bundle already
    holds -- a patch REPLACING a published document is a different operation from this one
    and the record check could not tell the two apart.
    """
    manifest = json.loads((patch_set / MANIFEST).read_text())
    prefix = base_uri(published)
    held = set(bundle.portable(published))
    out = []
    for entry in manifest["extractions"]:
        document, pointer = entry["document"], entry["pointer"]
        if document in held:
            raise ValueError(f"{document}: the published bundle already holds it")
        path = patch_set / DOCUMENTS / document
        if not path.is_file():
            raise ValueError(f"{document}: the patch set carries no such document")
        node = bundle.node_at(json.loads(path.read_text()), pointer)
        if not isinstance(node, dict):
            raise ValueError(f"{document}#{pointer} names no schema node")
        apart = frozenset((a["document"], a["pointer"]) for a in entry.get("apart", ()))
        # The bundle spells a WHOLE-DOCUMENT reference with no ``#`` at all -- 738 of its
        # 814 absolute references -- and the trailing ``#`` is not cosmetic: ``split_ref``
        # reads the delimiter, so the two spellings put the reference down different rows,
        # and the fragment row binds a SYMBOL where the document row binds the target's
        # whole shape.  Spell it the way the bundle does, or the patch is not the diff.
        uri = f"{prefix}{document}" + (f"#{pointer}" if pointer else "")
        out.append(Extraction(document, pointer, uri, node, apart))
    return tuple(out)


def _matches(node: Mapping, position: keywords.Position, held: Extraction) -> bool:
    """Does ``held``'s node account for every ACCEPTANCE keyword ``node`` states?

    Both halves are draft-07's, read through the one predicate ``record`` itself reads
    (:func:`codegen.bundle.is_an_annotation`), so there is no second list of which keyword
    decides acceptance:

    * every constraining keyword of the TARGET is already stated at the site, with the same
      value.  A target stating one the site does not would narrow the site;
    * every key of the SITE that the target does not state is an annotation.  Draft-07
      IGNORES a ``$ref``'s siblings, so a constraining key left beside one is a key the
      patched document stops asserting -- and ``_beside`` keeps it in the record, so the
      record check alone would pass over exactly that widening.

    An ANNOTATION on either side is free in both directions: the target's reaches the
    record only where the site states none, and the site's always wins.  That asymmetry is
    the one difference between the patched record and the published one, and it is
    reported rather than hidden -- see :func:`differing`.
    """
    if "$ref" in node:
        return False
    for key, value in held.subschema.items():
        if bundle.is_an_annotation(key, position):
            continue
        if key not in node or node[key] != value:
            return False
    return all(key in held.subschema or bundle.is_an_annotation(key, position) for key in node)


def rewritten(
    document: str,
    node: dict,
    extractions: Sequence[Extraction],
    pointer: str = "",
    position: keywords.Position = keywords.Position.ROOT,
) -> dict:
    """``node`` with every subschema an extraction accounts for replaced by a ``$ref``.

    The ROOT is never rewritten, at any depth: a document whose whole text became a
    reference would stop being the document the bundle publishes under that path, and no
    site this patch set extracts is a root.
    """
    done: dict[str, object] = {}
    for _, suffix, sub, at in bundle.subschemas(node):
        if not isinstance(sub, dict):
            continue
        here = f"{pointer}{suffix}"
        held = next(
            (
                e
                for e in extractions
                if (document, here) not in e.apart and _matches(sub, at, e)
            ),
            None,
        )
        if held is None:
            done[suffix] = rewritten(document, sub, extractions, here, at)
        else:
            # Every key the target does not ALREADY STATE IDENTICALLY stays at the site.
            # Dropping a key merely because the target also spells it would hand the
            # record the TARGET's value -- and a site's own ``description`` is the whole
            # reason the site is worth reading, so a rewrite that silently replaced 307
            # of them with one generic sentence would be a worse document than the one it
            # patched.  Keeping it is also what ``_beside`` expects: an annotation
            # sibling's value wins, so the site's text comes back out of the record.
            rest = {
                key: copy.deepcopy(value)
                for key, value in sub.items()
                if key not in held.subschema or held.subschema[key] != value
            }
            done[suffix] = {"$ref": held.uri, **rest}
    descended = {keyword for keyword, _, _, _ in bundle.subschemas(node)}
    return {
        key: bundle.rebuilt(key, value, done) if key in descended else copy.deepcopy(value)
        for key, value in node.items()
    }


def sites(published: Path, extractions: Sequence[Extraction]) -> list[tuple[str, str, str]]:
    """Every ``(document, pointer, uri)`` the patch turns into a reference, sorted.

    A function of the published bundle and the manifest, which is what makes the patch a
    handful of files rather than an 800-line list of pointers: the sites are DERIVED by the
    same match that rewrites them, so the manifest cannot name a site the rewrite misses or
    miss one it rewrites.
    """
    out = []
    for document in bundle.portable(published):
        doc = bundle.read(published, document)
        after_doc = rewritten(document, doc, extractions)
        for pointer, before in bundle.nodes(doc):
            after = bundle.node_at(after_doc, pointer)
            if isinstance(after, dict) and after.get("$ref") != before.get("$ref"):
                out.append((document, pointer, after["$ref"]))
    return sorted(out)


def stale(published: Path, extractions: Sequence[Extraction]) -> list[tuple[str, str]]:
    """Exclusions naming a site the shape no longer matches, sorted.

    A stale exclusion is the one way this manifest can rot silently: the day the site it
    names loses the shape, the entry stops excluding anything, and the next site to GAIN
    the shape at that pointer is rewritten with no one having looked at what it means.
    So the check asks for exactly what the exclusion claims -- that there IS a
    shape-matching site here and that it means something else.
    """
    out = []
    for held in extractions:
        bare = Extraction(held.document, held.pointer, held.uri, held.subschema, frozenset())
        for document, pointer in sorted(held.apart):
            doc = bundle.read(published, document) if (published / document).is_file() else None
            node = None if doc is None else bundle.node_at(doc, pointer)
            at = _position_of(doc, pointer) if isinstance(node, dict) else None
            if at is None or not isinstance(node, dict) or not _matches(node, at, bare):
                out.append((document, pointer))
    return sorted(out)


def _position_of(root: dict | None, pointer: str) -> keywords.Position | None:
    """The position the node at ``pointer`` occupies, by the one descent.

    A walk and not a reading of the pointer's text: the table decides what position a
    keyword holds its subschemas at, and ``/properties/x`` spells a PROP only because the
    table's row for ``properties`` says so.
    """
    if root is None:
        return None
    found: dict[str, keywords.Position] = {"": keywords.Position.ROOT}

    def walk(node: dict, at: str) -> None:
        for _, suffix, sub, position in bundle.subschemas(node):
            if isinstance(sub, dict):
                found[f"{at}{suffix}"] = position
                walk(sub, f"{at}{suffix}")

    walk(root, "")
    return found.get(pointer)


def apply(published: Path, patch_set: Path, out: Path) -> tuple[Extraction, ...]:
    """Write the patched bundle to ``out``: every published file, rewritten, plus the new ones.

    ``bundled/`` and ``mcp/`` are copied as they stand.  They are PROJECTIONS of the
    documents this rewrites, regenerated upstream from the same sources, so patching them
    here would state a second answer to a question the published bundle answers once --
    and nothing reads them (``bundle.portable`` excludes them, which is the population the
    record check ranges over).
    """
    extractions = load(patch_set, published)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(published, out)
    for document in bundle.portable(published):
        doc = rewritten(document, bundle.read(published, document), extractions)
        (out / document).write_text(json.dumps(doc, indent=2) + "\n")
    for held in extractions:
        destination = out / held.document
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(patch_set / DOCUMENTS / held.document, destination)
    return extractions


def census(published: Path, keyword: str = "pattern") -> dict[object, list[tuple[str, str]]]:
    """Every node stating ``keyword``, grouped by the value it states, over ``portable``.

    The measurement #8525 is built on, kept beside the patch it argues for so the figures
    in the issue are reproducible from the same walk the rewrite uses rather than from a
    script that no longer exists.
    """
    out: dict[object, list[tuple[str, str]]] = {}
    for document in bundle.portable(published):
        doc = bundle.read(published, document)
        for pointer, node in bundle.nodes(doc):
            if keyword in node:
                value = node[keyword]
                if isinstance(value, (str, int, float, bool)) or value is None:
                    out.setdefault(value, []).append((document, pointer))
    return out


class Difference(NamedTuple):
    """One pointer at which the published record and the patched one disagree.

    ``keys`` is what the disagreement IS ABOUT -- the keys one side states and the other
    does not, or the single key whose value changed -- and ``position`` is the position the
    node holding them occupies.  Together they are what :func:`seen_by_a_validator` reads,
    so classifying a difference needs no second list of which keyword decides acceptance.
    """

    document: str
    pointer: str
    keys: tuple[str, ...]
    position: keywords.Position | None
    detail: str

    def __str__(self) -> str:
        return f"{self.document}#{self.pointer or '/'}: {self.detail}"


def differing(published: Path, patched: Path) -> Iterator[Difference]:
    """Every pointer at which the two bundles' records disagree.

    THE ADMISSIBILITY CHECK of §1, and it is the patch's whole evidence.  Empty means the
    patch is byte-identical where it matters most: ``record`` inlines every cross-document
    reference, so resolving the patch returns the published document or this names the
    pointer at which it does not.

    Over ``bundle.portable(published)`` and never a written list (§9: a generic check does
    not hand-write the set it ranges over), so a document the patch touches and the author
    forgot cannot escape it.

    Byte-identity is taken over the CANONICAL serialisation -- object keys sorted, which is
    exactly the latitude RFC 8259 gives an object's members, and the one difference a
    rewrite is entitled to: an inlined target's keys arrive before the referring node's,
    where the published document wrote them in its own order.  Every other difference,
    including a list's order, is reported.

    KNOWN COST: :func:`codegen.bundle.record` is O(paths through the reference graph) and
    this takes 2,108 of them, which is minutes rather than seconds.  The population is the
    whole bundle and the check is the deliverable, so the cost is paid rather than sampled.
    """
    for document in bundle.portable(published):
        before, after = bundle.record(published, document), bundle.record(patched, document)
        if not isinstance(before, Mapping) or not isinstance(after, Mapping):
            if type(before) is not type(after) or before != after:
                yield Difference(
                    document, "", (), None,
                    f"the record is {before!r} published and {after!r} patched",
                )
            continue
        yield from _disagreements(document, "", before, after, _positions(after))


def seen_by_a_validator(found: Iterable[Difference]) -> list[Difference]:
    """Those differences a draft-07 validator can act on.

    The ACCEPTANCE half of the check, and it reads the same predicate ``record`` reads to
    decide a ``$ref``'s sibling (:func:`codegen.bundle.is_an_annotation`): a difference
    confined to keys whose cell compiles to no type, no field and no rule is a difference
    in what the document SAYS ABOUT ITSELF, and a difference at any other key is a
    difference in what it accepts.

    A patch leaving this empty has not forked the protocol.  It is strictly weaker than
    §1's byte-identity and is NOT a substitute for it -- both are reported, because which
    of the two is the admissibility line is a decision for the plan and not for its
    implementation.
    """
    return [
        d
        for d in found
        if d.position is None
        or not d.keys
        or any(not bundle.is_an_annotation(key, d.position) for key in d.keys)
    ]


def _positions(root: Mapping) -> dict[str, keywords.Position]:
    """Every pointer of ``root`` that holds a subschema, and the position it holds it at."""
    found: dict[str, keywords.Position] = {"": keywords.Position.ROOT}

    def walk(node: Mapping, at: str) -> None:
        for _, suffix, sub, position in bundle.subschemas(node):
            if isinstance(sub, dict):
                found[f"{at}{suffix}"] = position
                walk(sub, f"{at}{suffix}")

    walk(root, "")
    return found


def _canonical(node: object) -> str:
    return json.dumps(node, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _disagreements(
    document: str,
    pointer: str,
    before: object,
    after: object,
    at: Mapping[str, keywords.Position],
) -> Iterator[Difference]:
    """The deepest pointers at which two records disagree, and what differs there.

    A whole-record byte compare answers the question, and answers it as one unreadable
    diff; this walks into the mappings that agree on their key set so the failure names a
    POINTER, which is what a reviewer who does not trust us needs in order to check one.
    """
    if _canonical(before) == _canonical(after):
        return
    if isinstance(before, Mapping) and isinstance(after, Mapping):
        gained, lost = sorted(set(after) - set(before)), sorted(set(before) - set(after))
        if gained or lost:
            yield Difference(
                document,
                pointer,
                tuple(gained + lost),
                at.get(pointer),
                f"the patched node gains {gained} and loses {lost}",
            )
        # The SHARED keys are compared whether or not the key sets agreed.  Returning on
        # a key-set difference is how a changed VALUE hides behind an added key: the
        # rewrite that dropped a site's own ``description`` and let the target's stand in
        # its place reported here as a gain of ``$schema`` and ``title``, and the
        # substituted sentence was never looked at.
        for key in before.keys() & after.keys():
            yield from _disagreements(
                document, f"{pointer}/{bundle.escape_key(key)}", before[key], after[key], at
            )
        return
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        for index, (one, other) in enumerate(zip(before, after)):
            yield from _disagreements(document, f"{pointer}/{index}", one, other, at)
        return
    head, _, key = pointer.rpartition("/")
    yield Difference(
        document,
        pointer,
        (bundle.unescape_key(key),),
        at.get(head),
        f"{_canonical(before)} becomes {_canonical(after)}",
    )


def added(published: Path, patched: Path) -> list[str]:
    """The documents the patched bundle holds and the published one does not."""
    return sorted(set(bundle.portable(patched)) - set(bundle.portable(published)))


def removed(published: Path, patched: Path) -> list[str]:
    """The documents the published bundle holds and the patched one does not."""
    return sorted(set(bundle.portable(published)) - set(bundle.portable(patched)))


def report(published: Path, extractions: Collection[Extraction]) -> str:
    """One line per extraction: how many sites it takes, over how many documents."""
    found = sites(published, tuple(extractions))
    lines = []
    for held in extractions:
        mine = [s for s in found if s[2] == held.uri]
        lines.append(
            f"{len(mine):4d} sites  {len({d for d, _, _ in mine}):3d} docs  "
            f"{held.document}#{held.pointer}  {_canonical(held.subschema)}"
        )
    return "\n".join(lines)
