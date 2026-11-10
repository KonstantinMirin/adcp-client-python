"""**EVERY FAILING TEST OF UPSTREAM'S SUITE, ATTRIBUTED TO A NAMED CAUSE** -- so the pass
figure can be read.

    PYTHONPATH=.:src python -m survey suite_attribution --junit /srv/ws/scratch-attribute/m4.xml

**WHY THIS EXISTS.**  ``adcp-client-python-d09d`` measured 9,972 passed of upstream's 18,756
with the largest unclaimed block a block of pydantic ``ValidationError``\\ s, and said the
thing that matters about them: *"THEY MUST NOT BE ASSUMED TO BE OURS."*  Twice in one session
the naive reading blamed this compiler and was wrong -- ``Format.format_id`` was a WORD
falling through to the wrong subject, and the ``status`` family is upstream's generator
diverging from upstream's own schema.  A count with no attribution cannot tell those apart
from a real defect, so the figure means nothing until each failure names its cause.

**FOUR BUCKETS AND A FOURTH THAT IS HONEST** (:data:`BUCKETS`).  The attribution is derived,
never assigned: every bucket below is a question put to the DOCUMENT OF RECORD and to the two
trees' own text, and a pair no rule reaches is reported as ``unattributed`` rather than
pushed into whichever bucket is nearest.

**THE READING IS AT OUR CLASS'S OWN POINTER, which is what makes it exact.**  A failing test
names a WORD; that word resolves in this tree to a class, and the class carries
``__adcp_schema__ = SchemaRef(document, pointer)``.  So the question "does the document
require this field of this subject" needs no search and no match -- the class states the
position and ``adcp.types._base.applied_schema`` states the conjunction reaching it.  The
upstream half is read off their emitted text at ``2954b258b`` by
``survey.invented_defaults``, which resolves inheritance across modules; and the two halves
are compared, never averaged.

**NOTHING HERE FIXES ANYTHING.**  A class-3 finding is written out as a defect row with its
document pointer, for whoever owns that emission; an instrument that repaired its subject
could not be trusted about it.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parents[1]
for where in (ROOT, ROOT / "src"):
    if str(where) not in sys.path:
        sys.path.insert(0, str(where))

from survey import invented_defaults as inv  # noqa: E402

#: The four buckets ``adcp-client-python-d09d`` asks for, in its own words.
BUCKETS = {
    "upstream-laxness": (
        "the test needs upstream's generated class to admit something the document REFUSES "
        "-- a default the document does not state, or an explicit `null` at a property whose "
        "type does not admit one.  Such a test CANNOT pass against an implementation that "
        "honours the document, and no change to this compiler can make it pass without "
        "making an emitted type accept what the schema refuses"
    ),
    "wrong-subject": (
        "the WORD the test names resolves in this tree to a different subject than upstream's "
        "test means.  `adcp.types.Format` is upstream's HAND-WRITTEN "
        "`canonical_creative.Format`, which requires `format_kind` and `params`; ours is the "
        "document root `core/format.json#`, which requires `format_id` and `name`.  A seam "
        "defect, fixable, and not a disagreement with any document"
    ),
    "ours-diverges": (
        "our emitted class genuinely disagrees with the document of record: it requires a "
        "property the conjunction at its own pointer does not require, or refuses a value the "
        "document admits.  A REAL DEFECT of this compiler, reported with the pointer"
    ),
    "unattributed": (
        "no rule here reaches it.  Reported as itself rather than forced into a bucket, "
        "which is the whole discipline the three above are worth anything under"
    ),
    "not-ours-to-fix": (
        "upstream's DELETED GENERATORS -- `scripts.post_generate_fixes`, "
        "`scripts.consolidate_exports`, `scripts.generate_types`.  Counted and set aside: "
        "satisfying them would reinstate the generate-then-patch pipeline THE OUTCOME removes"
    ),
}

#: The head of a pydantic ``ValidationError`` message, which names the model and the count.
HEAD = re.compile(r"(\d+) validation errors? for (\S+)")

#: One error line's type, as pydantic spells it: ``[type=missing, input_value=...]``.
DETAIL = re.compile(r"\[type=([a-z_0-9]+)(?:,\s*input_value=(.*?))?(?:,\s*input_type=(\w+))?\]")

#: The pydantic error types that mean **a property the model requires is ABSENT**.  The two
#: spellings are pydantic's own: ``missing`` from a model field, ``required`` from a
#: ``jsonschema`` screen this package runs beside it.
ABSENT = ("missing", "required")

#: Upstream's deleted generators, whose import failures are nobody's (``d09d``).
DELETED = ("scripts.post_generate_fixes", "scripts.consolidate_exports", "scripts.generate_types")


class Triple(NamedTuple):
    """One error of one failing test: the model named, the location, the pydantic type."""

    model: str
    loc: str
    type: str
    input: str


class Failure(NamedTuple):
    """One failing or erroring test of the junit."""

    test: str
    head: str
    triples: tuple[Triple, ...]


class Finding(NamedTuple):
    """One attributed ``(model, field)``, with the two trees' readings beside the document's."""

    bucket: str
    why: str
    model: str
    field: str
    error: str
    tests: int
    document: str
    pointer: str
    document_says: str
    ours: str
    theirs: str


# ------------------------------------------------------------------------------- the junit


def failures(junit: Path) -> list[Failure]:
    """Every ``<failure>`` and ``<error>`` of a junit, with its pydantic errors parsed out.

    **THE ELEMENT TEXT AND NOT ONLY THE MESSAGE ATTRIBUTE, and the difference is measurable:
    pytest TRUNCATES the message.**  A three-error ValidationError arrives in ``message`` as
    one error and ``[+5 more lines; full report in element text]``; the body carries the whole
    report with pytest's ``E `` gutter on each line.  Measured on this junit: read from
    ``message`` alone, no test has more than TWO errors and the total is 966 -- against a
    message head that declares three for 124 of them.  So the report is read from the text,
    with the gutter stripped, and ``message`` is the fallback for an element with no body.
    """
    out: list[Failure] = []
    for case in ET.parse(junit).getroot().iter("testcase"):
        for child in case:
            if child.tag not in ("failure", "error"):
                continue
            message = child.get("message") or ""
            whole = _ungutter(child.text or "") or message
            test = f"{case.get('classname', '')}::{case.get('name', '')}"
            out.append(
                Failure(
                    test,
                    message.split("\n")[0][:160],
                    _triples(whole, message) or _triples(message, message),
                )
            )
    return out


def _ungutter(text: str) -> str:
    """pytest's ``E `` gutter stripped, so the traceback body reads as the report it holds."""
    kept = [line[2:] if line.startswith("E ") else line for line in text.splitlines()]
    return "\n".join(kept) if any(line.startswith("E ") for line in text.splitlines()) else ""


def _triples(text: str, message: str) -> tuple[Triple, ...]:
    """One ValidationError's ``(model, loc, type, input)`` errors, read out of ``text``.

    The location is the line ABOVE the ``[type=...]`` line, which is pydantic's own layout.
    ``()`` where there is no head -- it is not a validation error at all.

    **THE MODEL IS THE ``message`` HEAD'S AND THE ERRORS ARE THE TEXT'S, and the two have to
    be joined rather than each taken from wherever it is found first.**  A pytest traceback
    body carries the test's own source and sometimes a chained validation error, so the FIRST
    head in the text need not be the error the test failed on: measured on this junit, two
    findings were attributed to ``PrincipalDeclarationsState`` whose failing model was
    ``SyncPrincipalResponse`` -- the body mentioned the former higher up -- and both were
    reported as defects of ours against a document that declares no such property there.  So
    the head is taken from ``message``, which pytest writes from the exception itself, and the
    error list is read from the LAST head in the text naming that same model.
    """
    named = HEAD.search(message)
    if not named:
        return ()
    #: The model name can arrive with the next line glued on where pytest escaped the
    #: newline; the word is what is wanted and the rest is the first error's location.
    model = named.group(2).split("\\n")[0]
    found = None
    for candidate in HEAD.finditer(text):
        if candidate.group(2).split("\\n")[0] == model:
            found = candidate
    if found is None:
        return ()
    lines = text[found.end() :].split("\n")
    out: list[Triple] = []
    for index, line in enumerate(lines):
        detail = DETAIL.search(line)
        if detail:
            loc = lines[index - 1].strip() if index else ""
            out.append(Triple(model, loc, detail.group(1), (detail.group(2) or "").strip()))
    return tuple(out)


# ------------------------------------------------------------- the two trees and the document


def our_class(word: str) -> Any:
    """The class ``word`` names in this tree: the flat surface first, the emitted tree second.

    **THE FLAT SURFACE FIRST, because that is what upstream's test imports**: ``from
    adcp.types import Format`` is the statement whose subject is in question, and a reader
    that went looking for a class with that spelling would answer about a subject nobody
    imported.  The emitted tree is the fallback for a word the flat surface does not bind at
    all -- ``RequestSigning``, ``InternalOverlay`` -- and it is taken only where the spelling
    is UNIQUE there, because a word two modules declare reaches two subjects and picking one
    is the tie-break this reading refuses everywhere else.
    """
    try:
        flat = getattr(importlib.import_module("adcp.types"), word, None)
    except Exception:  # pragma: no cover - a surface that cannot import has no word
        flat = None
    if flat is not None:
        return flat
    found = [cls for cls in _emitted().get(word, ()) if getattr(cls, "__adcp_schema__", None)]
    return found[0] if len(found) == 1 else None


_EMITTED: dict[str, list[Any]] = {}


def _emitted() -> dict[str, list[Any]]:
    """``word -> every class of the emitted tree spelling it``, built once.

    Imported module by module rather than read as text, because what is wanted is the class's
    ``__adcp_schema__`` and its resolved ``model_fields`` -- the two things the text does not
    carry without re-resolving inheritance.
    """
    if _EMITTED:
        return _EMITTED
    import inspect

    for path in sorted((ROOT / "src" / "adcp" / "types" / "_schemas").rglob("*.py")):
        rel = path.relative_to(ROOT / "src").with_suffix("")
        name = ".".join(rel.parts[:-1] if rel.name == "__init__" else rel.parts)
        try:
            module = importlib.import_module(name)
        except Exception:  # pragma: no cover - a module that will not import binds no word
            continue
        for word, found in vars(module).items():
            if inspect.isclass(found) and getattr(found, "__module__", "") == name:
                _EMITTED.setdefault(word, []).append(found)
    return _EMITTED


def their_default(
    document: str, field: str, upstream: dict[str, inv.Decl], records: dict[str, dict]
) -> tuple[str, str]:
    """``(verdict, witness)`` for "does upstream default ``field`` in this document's module".

    **THE MODULE-WIDE READING, and it is what makes the ``status`` family attributable without
    a position match.**  Upstream's own word for an arm is an ordinal
    (``BuildCreativeResponse1``) and ours is a name (``BuildCreativeSuccess``), so the error's
    model name reaches no declaration of theirs -- and the first run reported 55 occurrences
    as ``unattributed`` for that reason alone.  But the question does not need the arm: every
    class upstream generated from ``media-buy/build-creative-response.json`` that declares
    ``status`` inherits it from ``core/protocol_envelope.ProtocolEnvelope``, where their
    generator wrote ``status: TaskStatus = TaskStatus.completed``.  So the reading is over the
    MODULE: ``"all"`` where every such class of theirs defaults it, ``"none"`` where none
    does, and ``"mixed"`` -- reported and not decided -- where they disagree.
    """
    defaulting: list[str] = []
    plain: list[str] = []
    for key, decl in upstream.items():
        if not decl.document or inv.document_for(decl.document, records) != document:
            continue
        found = inv.resolved(key, upstream).get(field)
        if found is None:
            continue
        (defaulting if found.defaulted else plain).append(key)
    if defaulting and not plain:
        witness = min(defaulting, key=len)
        whence = inv.resolved(witness, upstream)[field].whence
        return "all", f"{witness.rsplit('.', 1)[-1]} (default declared at {whence})"
    if plain and not defaulting:
        return "none", min(plain, key=len)
    if defaulting and plain:
        return "mixed", f"{len(defaulting)} default it, {len(plain)} do not"
    return "absent", ""


def where_bound(text: str, word: str) -> str:
    """What one module's text binds ``word`` to, as the dotted name on the right-hand side.

    Read for upstream's ``_eager.py``, whose ``Format = _canonical_creative.Format`` is the
    whole of the ``wrong-subject`` finding: their flat word names a HAND-WRITTEN class and
    ours names a document root, and the two require different properties.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{word} = "):
            return stripped[len(word) + 3 :].strip()
        if stripped.startswith(f"{word}: ") and " = " in stripped:
            return stripped.split(" = ", 1)[1].strip()
    return ""


def descend(record: dict, pointer: str, loc: str) -> tuple[str, str] | None:
    """``(the pointer of the object that declares the field, the field)``, or ``None``.

    **A pydantic LOCATION IS A PATH AND NOT A FIELD NAME**, and reading only its last segment
    is how a nested error gets attributed to the wrong object: ``ReportingObligation``'s
    error at ``schedule.period_anchor`` is a statement about the object at
    ``#/properties/schedule``, and asked at ``#`` the answer is "the document does not
    require ``period_anchor``" -- true, and about a different instance.  Measured: four of
    the fourteen ``ours-diverges`` findings of the first run were exactly this, and all four
    dissolved when the path was walked.

    Each non-final segment is a hop to ANOTHER instance -- ``/properties/<key>`` for a name
    and ``/items`` for an index -- and the hop is taken through
    ``adcp.types._base.applied_schema``, so a key the conjunction holds and the node's own
    text does not is still reached.  ``None`` where the walk does not resolve, which is this
    module's way of spelling "not attributable" rather than guessing a parent.
    """
    parts = [p for p in loc.split(".") if p]
    if not parts:
        return None
    at = pointer.lstrip("#")
    for part in parts[:-1]:
        step = "/items" if part.isdigit() else f"/properties/{inv_escape(part)}"
        try:
            node = applied_at(record, at + step)
        except inv._RAISES:
            return None
        if node is None:
            return None
        at += step
    return at, parts[-1]


def inv_escape(key: str) -> str:
    """One pointer segment, RFC 6901's two escapes -- ``codegen.bundle.escape_key``'s reading."""
    return key.replace("~", "~0").replace("/", "~1")


def applied_at(record: dict, pointer: str) -> dict | None:
    """The node the document applies at ``pointer``, or ``None`` where it holds none."""
    from adcp.types._base import applied_schema

    node = applied_schema(record, pointer)
    return node if isinstance(node, dict) else None


#: The keywords that hold a statement the instance must satisfy only UNDER A CONDITION.
#: ``if``/``then``/``else`` is draft-07's conditional; ``not`` is the same shape read the other
#: way round, and the bundle writes both (``core/reporting-obligation.json``).
CONDITIONAL = ("if", "then", "else", "not")


def _at(record: dict, pointer: str) -> object:
    """``pointer`` dereferenced against the record -- ``codegen.bundle.node_at``'s reading."""
    from codegen import bundle

    return bundle.node_at(record, pointer)


def conditionally_required(record: dict, pointer: str) -> frozenset[str]:
    """Properties the document requires at ``pointer`` only under a CONDITION.

    **THE THIRD READING OF REQUIREDNESS, and without it a correct enforcement reads as a
    defect of ours.**  ``core/reporting-obligation.json``'s ``schedule`` states *"if
    alignment is 'billing_cycle' then required: ['period_anchor', 'period_timezone']"*.  That
    is not in the node's own ``required`` list, so the unconditional reading answers "the
    document does not require it" -- and our class, which DOES enforce it, then reads as
    requiring a property the document does not.  Measured: all three ``ours-diverges``
    findings of the second run were this, and all three dissolved.

    ``datamodel-code-generator`` emits no ``if``/``then`` at all, so upstream's class carries
    none of these requirements -- which is why a test constructing the conditional's
    antecedent without its consequent passes there and cannot pass here.
    """
    out: set[str] = set()
    seen: set[int] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if id(node) in seen:
                return
            seen.add(id(node))
            for name in node.get("required") or ():
                if isinstance(name, str):
                    out.add(name)
            # **A ``$ref`` IS FOLLOWED HERE AND THAT IS NOT OPTIONAL.**
            # ``core/wholesale-feed-webhook.json``'s conditional reads
            # ``then: {"$ref": "#/definitions/Shared3"}`` and ``Shared3`` is
            # ``{"required": ["product_payload_view"]}`` -- the whole consequent is behind the
            # reference, so a walk that stopped at it would report the one statement the
            # document makes as a statement it does not make, and our enforcement of it as a
            # defect.  Measured: this was the last ``ours-diverges`` finding of the third run.
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#"):
                try:
                    walk(inv.through_the_store(_at(record, ref[1:]), record))
                except inv._RAISES:
                    pass
            for key, sub in node.items():
                if key in ("properties", "patternProperties", "definitions", "$ref"):
                    continue
                walk(sub)
        elif isinstance(node, list):
            for sub in node:
                walk(sub)

    for node in inv.conjoined(record, pointer):
        for key in CONDITIONAL:
            if key in node:
                walk(node[key])
    return frozenset(out) - inv.required_at(record, pointer)


def admits_null(node: Any) -> bool:
    """Does this property node admit an explicit JSON ``null``?

    A node with no ``type`` at all admits one -- the document constrains nothing there -- and
    so does a ``type`` list holding ``"null"`` or a disjunction with a ``{"type":"null"}``
    arm.  Anything else REFUSES it, which is draft-07's own reading and the question the
    explicit-null family turns on.
    """
    if not isinstance(node, dict):
        return True
    declared = node.get("type")
    if isinstance(declared, str):
        return declared == "null"
    if isinstance(declared, list):
        return "null" in declared
    #: **A DISJUNCTION WITH NO NULL ARM REFUSES, and the clause below must not reach it.**
    #: ``core/mcp-webhook-payload.json``'s ``result`` states an ``anyOf`` and no ``type``, so a
    #: reader that fell through to "no ``type`` means unconstrained" would call it
    #: null-admitting and report our refusal as a defect.  A node that states a disjunction
    #: has stated its admissible set.
    for keyword in ("anyOf", "oneOf"):
        held = node.get(keyword)
        if isinstance(held, list) and held:
            return any(admits_null(a) for a in held)
    return "type" not in node and not node.get("enum") and "const" not in node


# -------------------------------------------------------------------------- the attribution


def attribute(
    triple: Triple,
    tests: int,
    upstream: dict[str, inv.Decl],
    records: dict[str, dict],
    their_flat: dict[str, str],
) -> Finding:
    """One ``(model, field, error type)`` attributed, with every reading it was decided on.

    The order of the questions is the order of the evidence, and it is deliberate: the WORD
    is checked before the document, because a word resolving to the wrong subject makes every
    document reading below it a reading about the wrong class.
    """
    field = triple.loc.split(".")[-1]
    ours = our_class(triple.model)
    held = getattr(ours, "__adcp_schema__", None)
    document = getattr(held, "document", "") or ""
    pointer = getattr(held, "pointer", "") or ""

    #: **THE WORD, FIRST.**  Upstream's flat surface says what their test's name means.  A
    #: word their `_eager.py` binds to a hand-written module and ours binds to a document
    #: class is two subjects, and the properties they require differ for that reason alone.
    theirs_flat = their_flat.get(triple.model, "")
    hand_written = theirs_flat and ".domains." not in theirs_flat
    if hand_written and document:
        # **AND WHETHER RESTORING THE WORD WOULD RESCUE THE TEST IS A SECOND QUESTION.**
        # ``adcp-client-python-eknd``'s own ruling: upstream uses those hand-written classes
        # as SUBCLASSES of their generated arm, so a restored one subclasses OURS and
        # inherits the requiredness the document states -- "the tests that construct a
        # response WITHOUT status still fail, because our class requires what the document
        # requires".  So a `missing` error on a property the document requires is BOTH a
        # wrong subject and upstream's laxness, and naming only the first would promise a
        # rescue the restore cannot deliver.
        also = ""
        record = records.get(document)
        inherits = _inherits_a_document_class(theirs_flat, upstream)
        if record is not None and triple.type in ABSENT and inherits:
            try:
                if field in inv.required_at(record, pointer.lstrip("#")):
                    verdict, witness = their_default(document, field, upstream, records)
                    also = (
                        f"; AND the document requires {field} at {pointer} "
                        f"(upstream's side reads {verdict!r}{': ' + witness if witness else ''}) "
                        f"while their hand-written class BASES on {inherits}, so restoring the "
                        "word does NOT rescue this test -- the restored class subclasses ours "
                        "and inherits the requirement (eknd's own clause)"
                    )
            except inv._RAISES:
                also = "; the document's conjunction at this pointer could not be read"
        elif not inherits:
            also = (
                "; their hand-written class bases on NO generated class, so the restore "
                "replaces the subject outright and the document's requirement at our pointer "
                "does not reach it"
            )
        return Finding(
            "wrong-subject",
            f"upstream's flat {triple.model} is {theirs_flat} (hand-written, no document); "
            f"ours is {document}{pointer}{also}",
            triple.model,
            field,
            triple.type,
            tests,
            document,
            pointer,
            "n/a -- the two words name different subjects",
            _declares(ours, field),
            theirs_flat,
        )

    their_decl = _their_class(triple.model, upstream)
    #: **UPSTREAM'S FIELD IS ONLY THEIR CLASS'S FIELD WHERE THE ERROR IS AT ITS OWN LEVEL.**
    #: A nested location names an object their generator emitted as some OTHER class, and
    #: reading the top-level class's field of that name would answer about a different
    #: subject -- the same mistake the unwalked location makes on the document's side.
    nested = len([p for p in triple.loc.split(".") if p]) > 1
    their_field = (
        inv.resolved(their_decl, upstream).get(field)
        if their_decl in upstream and not nested
        else None
    )
    record = records.get(document) if document else None
    if record is None:
        #: **A WORD NEITHER TREE DECLARES IS THE TEST'S OWN**, and saying so is the whole
        #: difference between "unattributed" and "attributed to the test".  Upstream's
        #: ``tests/test_targeting_overlay_compat.py`` declares ``class InternalOverlay(base)``
        #: in the test body, so the failing subject is a subclass of whichever tree class the
        #: test reached -- the error is about THAT base's field and the word names nothing of
        #: either tree.  Measured: ``InternalOverlay``, ``Customized``, ``Envelope`` and
        #: ``OrdinaryParent``, 29 occurrences.
        mine = "declared by neither tree" if not their_decl else f"theirs: {their_decl}"
        return Finding(
            "unattributed",
            "no class of this tree's flat surface or emitted tree spells the word uniquely "
            f"({mine}) -- a subject the TEST declares, so the error is about whichever base "
            "it subclassed and there is no position of a document to read it at",
            triple.model,
            field,
            triple.type,
            tests,
            document,
            pointer,
            "",
            _declares(ours, field),
            their_decl if their_decl in upstream else "",
        )

    walked = descend(record, pointer, triple.loc)
    if walked is None:
        return Finding(
            "unattributed",
            f"the error's location {triple.loc!r} is not a path this walk resolves from "
            f"{pointer} -- an empty location (the error is about the whole model, usually a "
            "union that matched no arm) or a segment the document does not hold",
            triple.model,
            triple.loc,
            triple.type,
            tests,
            document,
            pointer,
            "",
            _declares(ours, field),
            their_decl if their_decl in upstream else "",
        )
    at, field = walked
    try:
        required = inv.required_at(record, at)
        nodes = inv.properties_spanning(record, at).get(field, [])
    except inv._RAISES:
        return Finding(
            "unattributed",
            f"the document's conjunction at #{at} could not be read",
            triple.model,
            field,
            triple.type,
            tests,
            document,
            pointer,
            "",
            _declares(ours, field),
            their_decl if their_decl in upstream else "",
        )
    pointer = f"#{at}"

    if triple.type in ABSENT:
        says = "required" if field in required else "not required"
        if field in required:
            if their_field is not None and their_field.defaulted:
                return Finding(
                    "upstream-laxness",
                    f"the conjunction at {pointer} REQUIRES {field} and upstream's "
                    f"{their_decl.rsplit('.', 1)[-1]} defaults it "
                    f"(declared at {their_field.whence.rsplit('.', 1)[-1]})",
                    triple.model,
                    field,
                    triple.type,
                    tests,
                    document,
                    pointer,
                    f"required, {_states(nodes)}",
                    "required (no default)",
                    f"default={their_field.default or 'unread'}",
                )
            verdict, witness = their_default(document, field, upstream, records)
            if verdict == "all":
                return Finding(
                    "upstream-laxness",
                    f"the conjunction at {pointer} REQUIRES {field}, and EVERY class "
                    f"upstream generated from {document} that declares {field} defaults it "
                    f"-- {witness}",
                    triple.model,
                    field,
                    triple.type,
                    tests,
                    document,
                    pointer,
                    f"required, {_states(nodes)}",
                    "required (no default)",
                    f"defaulted module-wide: {witness}",
                )
            return Finding(
                "unattributed",
                f"the document requires the property; upstream's side reads {verdict!r}"
                + (
                    " and the location is NESTED, so the subject is a class their generator "
                    "named elsewhere"
                    if nested
                    else ""
                ),
                triple.model,
                field,
                triple.type,
                tests,
                document,
                pointer,
                says,
                "required (no default)",
                f"{verdict}: {witness}" if witness else verdict,
            )
        if field in conditionally_required(record, at):
            return Finding(
                "upstream-laxness",
                f"the document states the requirement for {field} at {pointer} under an "
                "if/then CONDITIONAL, which our class enforces and which "
                "datamodel-code-generator does not emit at all -- so upstream's class "
                "carries no such requirement and the test's payload is one the document "
                "refuses",
                triple.model,
                field,
                triple.type,
                tests,
                document,
                pointer,
                "required under a conditional (if/then)",
                "enforced",
                "no conditional emitted",
            )
        return Finding(
            "ours-diverges",
            f"the conjunction at {pointer} does NOT require {field}, conditionally or "
            "otherwise, and our class does",
            triple.model,
            field,
            triple.type,
            tests,
            document,
            pointer,
            says,
            "required",
            f"default={their_field.default}" if their_field is not None else "not declared",
        )

    if triple.input == "None":
        if not nodes:
            return Finding(
                "unattributed",
                f"the document declares no property {field} at {pointer} at all, so it "
                "states nothing about a null there -- the question is why our class carries "
                "the field, not whether the document admits the value",
                triple.model,
                field,
                triple.type,
                tests,
                document,
                pointer,
                "no such property",
                _declares(ours, field),
                their_decl if their_decl in upstream else "",
            )
        if any(admits_null(n) for n in nodes):
            return Finding(
                "ours-diverges",
                f"the document at {pointer} ADMITS null at {field} and our class refuses it",
                triple.model,
                field,
                triple.type,
                tests,
                document,
                pointer,
                f"admits null: {_states(nodes)}",
                f"refuses null ({triple.type})",
                "admits null" if their_field is not None else "not declared",
            )
        return Finding(
            "upstream-laxness",
            f"the document at {pointer} REFUSES an explicit null at {field} "
            f"({_states(nodes)}) and the test sends one",
            triple.model,
            field,
            triple.type,
            tests,
            document,
            pointer,
            f"refuses null: {_states(nodes)}",
            f"refuses null ({triple.type})",
            "admits null" if their_field is not None else "not declared",
        )

    return Finding(
        "unattributed",
        f"a {triple.type} error whose input is {triple.input[:40]!r} -- not an absent "
        "property and not an explicit null, so neither rule here reaches it",
        triple.model,
        field,
        triple.type,
        tests,
        document,
        pointer,
        _states(nodes),
        _declares(ours, field),
        "",
    )


def _inherits_a_document_class(dotted: str, upstream: dict[str, inv.Decl]) -> str:
    """The GENERATED base of one of upstream's hand-written classes, or ``""``.

    **WHETHER A RESTORE RESCUES A TEST TURNS ON THIS AND NOTHING ELSE.**
    ``canonical_creative.Format(CanonicalBoundaryModel)`` bases on nothing generated, so
    restoring the word replaces the subject outright and ``core/format.json``'s
    ``required: ['format_id', 'name']`` never reaches it -- the 302 ``Format`` errors go away.
    ``canonical_creative.GetCreativeDeliveryResponse(_LegacyGetCreativeDeliveryResponse,
    CanonicalBoundaryModel)`` bases on their generated arm, which under
    ``adcp-client-python-eknd``'s ruling becomes OUR class -- so the restored class inherits
    the document's requirement and the 33 ``status`` errors survive the restore.  Reading only
    "the word is wrong" would promise a rescue for both.
    """
    word = dotted.split(".")[-1]
    key = next(
        (k for k in upstream if k.endswith(f".canonical_creative.{word}")),
        f"adcp.types.canonical_creative.{word}",
    )
    decl = upstream.get(key)
    if decl is None:
        return ""
    for base in decl.bases:
        found = upstream.get(base)
        if found is not None and found.document:
            return f"{base.rsplit('.', 1)[-1]} ({found.document})"
    return ""


def _their_class(word: str, upstream: dict[str, inv.Decl]) -> str:
    """The one of upstream's declarations spelling ``word``, or ``""`` where it is not unique.

    Uniqueness is the gate, exactly as ``codegen.structure.bind``'s is: a word two of their
    modules declare reaches two subjects, and picking one would be the tie-break this whole
    reading refuses.
    """
    found = [k for k in upstream if k.rsplit(".", 1)[-1] == word]
    return found[0] if len(found) == 1 else ""


def _declares(cls: Any, field: str) -> str:
    """What our class states about ``field``: required, defaulted, or not declared."""
    fields = getattr(cls, "model_fields", None)
    if not isinstance(fields, dict) or field not in fields:
        return "not declared"
    return "required" if fields[field].is_required() else "optional"


def _states(nodes: list[dict]) -> str:
    """What the document states at a property, as the keywords that bear on admissibility."""
    keep = ("type", "const", "enum", "default", "anyOf", "oneOf", "format")
    out: dict[str, Any] = {}
    for node in nodes:
        for key in keep:
            if key in node and key not in out:
                out[key] = node[key] if key not in ("anyOf", "oneOf") else f"{len(node[key])} arms"
    return json.dumps(out, sort_keys=True, default=str)[:200] or "nothing"


# ------------------------------------------------------------------------------- the report


def census(found: list[Failure]) -> collections.Counter[str]:
    """The failing suite by named cause -- ``d09d``'s own ranking, re-derived."""
    out: collections.Counter[str] = collections.Counter()
    for failure in found:
        if failure.triples:
            out["pydantic ValidationError"] += 1
        elif any(name in failure.head for name in DELETED):
            out["upstream's DELETED GENERATORS (not ours)"] += 1
        elif "Regex pattern did not match" in failure.head:
            out["AssertionError: Regex pattern did not match"] += 1
        elif "DID NOT RAISE" in failure.head:
            out["Failed: DID NOT RAISE"] += 1
        elif "assert None is True" in failure.head:
            out["assert None is True"] += 1
        elif "GetProductsField" in failure.head:
            out["GetProductsField (in flight, emission)"] += 1
        elif failure.head.startswith("AttributeError") or "has no attribute" in failure.head:
            out["AttributeError on the flat surface"] += 1
        elif failure.head.startswith(("ImportError", "ModuleNotFoundError")):
            out["ImportError / ModuleNotFoundError"] += 1
        else:
            out["other"] += 1
    return out


def digest(findings: list[Finding]) -> str:
    """A digest of the attributed SET's membership, not of its size."""
    canonical = json.dumps(
        sorted((f.bucket, f.model, f.field, f.error) for f in findings), sort_keys=True
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:20]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--revision", default=inv.REVISION)
    parser.add_argument("--records", type=Path, default=inv.RECORDS)
    parser.add_argument("--table", type=Path, default=None)
    args = parser.parse_args(argv)

    found = failures(args.junit)
    ranking = census(found)
    print(f"{len(found)} failing or erroring tests in {args.junit}")
    for cause, n in ranking.most_common():
        print(f"  {n:5d}  {cause}")

    src = inv.sources(args.revision, ROOT)
    upstream = inv.declarations(src)
    records = inv.records_of(args.records)
    their_flat = {
        word: where_bound(src.get("adcp.types._eager", ""), word)
        for word in {t.model for f in found for t in f.triples}
    }

    #: Counted per (model, field, type), with the number of TESTS each accounts for, because
    #: a cause is a cause once and a test is a test once and the two are different figures.
    per: collections.Counter[tuple[str, str, str]] = collections.Counter()
    for failure in found:
        for triple in failure.triples:
            per[(triple.model, triple.loc, triple.type)] += 1
    findings = [
        attribute(
            Triple(model, loc, kind, _input_of(found, model, loc, kind)),
            n,
            upstream,
            records,
            their_flat,
        )
        for (model, loc, kind), n in sorted(per.items(), key=lambda kv: -kv[1])
    ]

    buckets: collections.Counter[str] = collections.Counter()
    errors: collections.Counter[str] = collections.Counter()
    for finding in findings:
        buckets[finding.bucket] += finding.tests
        errors[finding.bucket] += 1
    print(
        f"\nValidationError errors attributed: {sum(errors.values())} distinct, "
        f"{sum(buckets.values())} occurrences"
    )
    for bucket, n in buckets.most_common():
        print(f"  {n:5d} occurrences / {errors[bucket]:3d} distinct  {bucket}")
    print(f"digest {digest(findings)}")

    #: **AND THE TEST-LEVEL COUNT, which is the one the pass figure is in.**  A test carries
    #: several errors and a cause is a cause once, so the two figures are different and
    #: reporting only the first would answer a question nobody asked: what moves the pass
    #: column is a TEST, and a test is attributable only where EVERY error it raised is.  One
    #: whose errors fall in two buckets is reported as ``mixed`` and never counted in either.
    by_error = {(f.model, f.field, f.error): f.bucket for f in findings}
    at_test: collections.Counter[str] = collections.Counter()
    for failure in found:
        if not failure.triples:
            continue
        reached = {
            by_error.get((t.model, t.loc.split(".")[-1], t.type))
            or by_error.get((t.model, t.loc, t.type))
            or "unattributed"
            for t in failure.triples
        }
        at_test[
            "mixed: " + "+".join(sorted(reached)) if len(reached) > 1 else next(iter(reached))
        ] += 1
    print(f"\nby TEST ({sum(at_test.values())} ValidationError tests):")
    for bucket, n in at_test.most_common():
        print(f"  {n:5d}  {bucket}")

    for bucket in ("ours-diverges", "unattributed"):
        rows = [f for f in findings if f.bucket == bucket]
        if rows:
            print(f"\n{bucket.upper()} ({len(rows)}):")
            for f in sorted(rows, key=lambda r: -r.tests):
                print(f"  {f.tests:4d}  {f.model}.{f.field} [{f.error}] {f.document}{f.pointer}")
                print(f"        {f.why}")

    if args.table:
        lines = ["\t".join(Finding._fields)]
        lines += ["\t".join(str(v).replace("\t", " ") for v in f) for f in findings]
        args.table.write_text("\n".join(lines) + "\n")
        print(f"\n-> {args.table}")
    return 0


def _input_of(found: list[Failure], model: str, loc: str, kind: str) -> str:
    """The ``input_value`` the first occurrence of this error carried."""
    for failure in found:
        for triple in failure.triples:
            if (triple.model, triple.loc, triple.type) == (model, loc, kind):
                return triple.input
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
