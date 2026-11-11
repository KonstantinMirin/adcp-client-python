"""**EVERY SEGMENT OF EVERY STAMPED POINTER IS A POSITION ITS DOCUMENT HOLDS.**

``docs/plan/architecture.md`` §9: *"do not decide a position the bundle does not hold from
a view of it."*  A class's ``__adcp_schema__`` is the claim it makes about WHICH NODE OF
WHICH DOCUMENT it is, and a pointer naming a path the document does not contain is that
rule broken -- the class is stamped where its document states nothing.

``adcp-client-python-8awh`` is the row, and the defect it reports is a SPLICE: §5's
distribution gives a composing node one class per branch of a ``$ref`` target's own
combinator, and the pointer was built by composing the REFERENCING path with the TARGET's
child index.  Measured before the fix, by this file's own predicate: **70 classes over 12
documents** -- 16 ``adagents.json``, 16 ``core/package-format-snapshot.json``, 10
``core/postal-area.json``, 6 ``core/async-response-data.json``, 5
``core/vendor-pricing-option.json``, 3 each ``core/package-signal-targeting.json``,
``core/product-filters.json`` and ``media-buy/build-creative-request.json``, and 2 each
``core/creative-representation.json``, ``creative/sync-creatives-request.json``,
``media-buy/buy-products-request.json`` and ``media-buy/request-proposals-request.json``.

**THE PREDICATE IS THE RAW DOCUMENT AND NOT THE RECORD, and the difference is the whole
reason this file exists beside the other two readings.**  Three walks reach three answers
over the same stamps, and only the first answers the question §9 asks:

====================================================  ==========================  =====
walk                                                  what it is                  failed
====================================================  ==========================  =====
``bundle.read`` segment by segment                    the DOCUMENT, as published  70
``bundle.node_at`` + the record's storage hop         the RECORD, a view of it     4
``applied_schema``                                    the record plus substitution 0
====================================================  ==========================  =====

The record INLINES every cross-document ``$ref`` (``bundle.record``), so a referencing
path extended by the target's child index resolves there -- which is why 66 of the 70
looked sound and why ``distributed_pointer``'s docstring claimed §9 was satisfied while
quoting it.  **A view that makes a position reachable is exactly what §9's sentence names**,
so the published document is the subject and nothing is followed here: not a
cross-document reference, not the record's own storage hop, not ``applied_schema``'s
substitution of a conjoined statement's value for a key the node's text does not spell.

**AND THE SUBJECT IS THE STAMP, NEVER THE WALK'S ADDRESS.**  ``Emitted.declared`` is keyed
by the pointer the walk ADDRESSES a node by -- ``Module.declared``, ``Module.shapes``,
``Module.hops``, ``Module.at`` and every ``ir.TypeRef(pointer, local=True)`` share that key
-- and §5's distribution needs it distinct per product, so the splice survives there BY
DESIGN (``lower.composition.distributed_pointer``, whose docstring is where the two are
told apart).  Read over that record this clause would report 10 addresses and call them
defects.  What a consumer sees, what ``schema_at`` resolves and what §9 is about is the
``__adcp_schema__`` a CLASS carries, so that is what is read: the loaded tree's own
classes.

**KEYED ON THE POINTER AND NEVER ON A CLASS NAME.**  The finding set is
``(document, pointer)`` pairs, so a run that renames a class -- which the positional-name
ruling is doing to several of these very documents -- moves nothing here.  A symbol appears
in the failure MESSAGE as a hint for whoever reads it and in no assertion.

**DERIVED OVER THE WHOLE TREE AND ASSERTED NON-EMPTY FIRST.**  ``docs/plan/final-state.md``:
*"A READING HOLDS OR IT DOES NOT.  Never M of N."*  So there is no ceiling, no allowlist
and no list of the twelve documents -- the population is every class of the loaded tree
that carries a stamp, and the first clause is that there are some, because a predicate over
an empty set passes every assertion below while saying nothing.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Mapping, Sequence
from typing import Any

import fresh
import pytest
from nodeset import claimed

import adcp.types._schemas as schemas_pkg
from adcp.types._base import SchemaRef
from codegen import bundle

#: One spelling of the bundle, re-exported from ``tests_emit/fresh.py``: a file that spells
#: its own path can come to range over a different bundle from the tree it reads.
BUNDLE = fresh.BUNDLE


def _held(document: Mapping[str, Any], pointer: str) -> str | None:
    """``None`` where every segment of ``pointer`` is a position ``document`` holds, or the
    reason it is not.

    draft-07's own addressing and nothing else: a segment indexes a mapping by key or an
    array by position, and ``bundle.unescape_key`` is the one reading of ``~0``/``~1``
    this project has.  **Nothing is followed.**  A ``$ref`` is a node's own statement and
    not a hop the addressing takes, so a pointer that needs one followed to resolve is
    naming a position another document holds.
    """
    at: Any = document
    seen = ""
    for part in [p for p in pointer.lstrip("#").split("/") if p]:
        key = bundle.unescape_key(part)
        if isinstance(at, Mapping) and key in at:
            at = at[key]
        elif (
            isinstance(at, Sequence)
            and not isinstance(at, (str, bytes))
            and part.isdigit()
            and int(part) < len(at)
        ):
            at = at[int(part)]
        else:
            return f"{seen or '#'} states no {key!r}"
        seen = f"{seen}/{part}"
    return None


@pytest.fixture(scope="module")
def stamped() -> dict[tuple[str, str], str]:
    """Every ``(document, pointer)`` the LOADED tree stamps, with one symbol as a hint.

    Off the loaded classes and never off the emitted text or off ``Emitted.declared``: the
    module docstring says why each of the other two is a different subject.  A class
    DECLARES its own stamp (``cls.__dict__``), so an inheriting class is not counted twice
    for the one its base carries -- which is the same reading
    ``BranchDispatchMixin._dispatching`` makes of ``_branch_models`` and for the same
    reason.

    The value is a symbol and the KEY is the pair, so two classes at one pointer collapse
    here rather than being reported twice: this clause is about the pointer, and
    ``tests_emit/test_one_node_is_one_declaration.py`` is where one-class-per-node lives.
    """
    assert not fresh.FAILURE, fresh.FAILURE
    out: dict[tuple[str, str], str] = {}
    unimportable: dict[str, str] = {}
    for info in pkgutil.walk_packages(schemas_pkg.__path__, schemas_pkg.__name__ + "."):
        try:
            module = importlib.import_module(info.name)
        except Exception as why:  # noqa: BLE001 -- the absence IS the finding
            unimportable[info.name] = f"{type(why).__name__}: {why}"
            continue
        for obj in vars(module).values():
            if not isinstance(obj, type):
                continue
            ref = obj.__dict__.get("__adcp_schema__")
            if isinstance(ref, SchemaRef):
                out.setdefault((ref.document, ref.pointer), obj.__name__)
    assert not unimportable, unimportable
    return out


def test_the_tree_stamps_something(stamped: dict[tuple[str, str], str]) -> None:
    """The population, asserted before anything is asserted OVER it.

    A module that failed to import contributes no stamp, and a reading that took the
    absence for a clean answer would report green on a tree nothing could load -- which is
    why the fixture raises on an unimportable module rather than skipping it
    (``final-state.md``: a gate that disappears with its own instrument reports green).
    """
    claimed("classes the tree stamps with a schema reference", stamped)
    assert len({d for d, _ in stamped}) > 1, sorted({d for d, _ in stamped})


def test_every_stamped_pointer_is_a_position_its_document_holds(
    stamped: dict[tuple[str, str], str],
) -> None:
    """The obligation, over every stamp of the tree and named by pointer where it fails.

    **The documents are read ONCE each** and the pairs are grouped by document, because
    the subject is the published text and re-reading it per class would make the cost the
    product rather than the sum.

    A document no bundle holds is a finding of its own and not an exemption: a stamp names
    a document and a resource path inside the package, so a stamp naming neither is a
    class a consumer cannot resolve at all.
    """
    portable = set(bundle.portable(BUNDLE))
    documents: dict[str, Mapping[str, Any]] = {}
    nowhere: dict[str, str] = {}
    for document, pointer in sorted(stamped):
        if document not in documents:
            if document not in portable:
                nowhere[f"{document}{pointer}"] = (
                    f"the bundle does not hold {document!r} at all"
                )
                continue
            documents[document] = bundle.read(BUNDLE, document)
        why = _held(documents[document], pointer)
        if why is not None:
            nowhere[f"{document}{pointer}"] = f"{why} (stamped on {stamped[(document, pointer)]})"
    assert not nowhere, nowhere
