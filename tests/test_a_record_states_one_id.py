"""A RECORD STATES ONE ``$id`` -- the one of the document it IS -- and the hoisted
storage stays reachable from inside every inlined copy.

``adcp-client-python-bfqk``.  ``bundle.record`` inlined a referenced document's node
INCLUDING its root ``$id``, and draft-07 reads a ``$id`` at a schema position as a NEW
BASE URI for everything under it.  ``bundle.stored`` then hoists each repeated subtree
to ``#/definitions/SharedN`` and writes a local reference at every occurrence -- and an
occurrence lying under an inlined copy's ``$id`` resolves against THAT copy's base
rather than against the record root that holds the section:

    _WrappedReferencingError: PointerToNowhere: '/definitions/Shared2' does not exist
    within {'$id': '.../core/frequency-cap-impression-constraints.json', ...}

**IT WAS THE SHIPPED HALF, and that is why this file grades a payload and not a text.**
``_base.store_expanded`` is applied at the ACCESSOR (``schema_at``) and not at
``_refuse_at``, so a reader that WALKS a node never meets a storage reference and
``strict_validate`` -- the half a consumer runs -- meets every one of them.  A consumer
validating against an affected class got ``PointerToNowhere`` instead of a verdict, for
every payload.

**MEASURED IN BOTH DIRECTIONS, and it is a defect of OURS rather than of a bundle.**
The row was filed against bundle 3.3, whose 1,138 portable documents all state a root
``$id``, on the premise that 3.2 states none.  3.2 states none because WE STRIPPED THEM
(``schemas/cache/3.2.provenance.json``; ``adcp-client-python-82m.48``).  Put one back:

* **a faithful 3.2** -- upstream ``c34931a08``'s committed ``dist/schemas/3.2.4``, untouched
  -- grades 849 pass -> 800 pass over the same 2,589 pairs, and **54 of the 55 pairs that
  move are this defect**, over 33 distinct documents of the 1,059 portable and 20 distinct
  printed scopes (``core/error.json`` 19, ``core/macro-encoding.json`` 4,
  ``core/reporting-adjustment-receipt.json`` 4, ``core/reporting-consumer-status.json`` 4);
* **one added line on ONE committed 3.2 document** -- the root ``$id`` of
  ``core/frequency-cap-impression-constraints.json``, with ``diff -rq`` over the two
  1,625-document trees naming that file and no other -- takes
  ``core/frequency-cap-constraints.json#`` from ``verdict=pass`` to
  ``verdict=fail:accepts:model_error`` with ``PointerToNowhere: '/definitions/Shared2'``;
* on bundle 3.3 the same defect accounts for 43 failing pairs.

**THE RULE, and it is a statement about OUR RENDERING rather than about any bundle.**  An
``$id`` names where a document LIVES.  An inlined copy does not live there -- it is text
the record quotes -- so a record stating 730 of them (measured: 730 of bundle 3.3's 733
cross-document-referencing records, before the repair) states 729 falsehoods about itself.
``recorded`` keeps the ``$id`` of the document the record IS, at the record root, where it
is true and where it re-bases nothing: the base URI never moves below the root, so
``#/definitions/SharedN`` resolves against the root that holds the section, always.

**NOT ``_refuse_at`` CALLING ``store_expanded``**, which was the other candidate: it pays
``store_expanded``'s whole cost on every validation a consumer runs -- the record of
``core/mcp-webhook-payload.json`` is 6,442 distinct nodes carrying 957,187 -- to answer a
question the record should not have been asking.  And it would leave the record stating the
falsehood, so every other reader of a carried record would still have to reason about a
base URI that moves.

**THE STRIP IS BY POSITION AND NEVER BY THE KEY'S SPELLING**, which is
``adcp-client-python-xvk3``'s measurement read forward.  The vendor transform that produced
``schemas/cache/3.2`` removed every dict key spelled ``$id`` recursively, and in 1 of 1,625
documents that key is not an annotation but a ``properties`` ENTRY:
``extensions/extension-meta.json`` is the schema for an extension FILE, and an extension
file declares its own id.  The strip deleted the entry and left the document REQUIRING a
property it declares no schema for, so one required SDK field carries ``Any`` where the
document states ``^/schemas/extensions/[a-z][a-z0-9_]*\\.json$``.  ``recorded`` descends by
``keywords``' own table (``bundle.subschemas``), so it drops a ``$id`` the node STATES and
never one a node is keyed by -- and the third check below is that fact graded rather than
asserted.
"""

from __future__ import annotations

import contextlib
import importlib
import json
import socket
import sys
from collections.abc import Iterator
from pathlib import Path

import fresh
import jsonschema
import pytest
from nodeset import claimed, ratchet

from adcp.types import _base
from codegen import bundle, emit
from codegen.refusal import Refusal

#: The second bundle, taken from the ONE declaration (``tests/fresh.py``) -- the only
#: committed bundle that states a ``$id`` at all, because 3.2's were stripped.
SECOND = fresh.SECOND

DRAFT = "http://json-schema.org/draft-07/schema#"

#: The base the constructed bundle below spells its own references and identifiers with.
#: A version nobody publishes, for ``test_fragment_ref``'s reason: a reference that
#: resolved to a real document would make the check a reading of the network.
BASE = "https://adcontextprotocol.org/schemas/9.9.9/"

#: The REPEATED subtree, stated at a schema position in BOTH documents below, which is
#: what gives its interned content two in-edges and makes ``bundle.stored`` hoist it
#: (``stored``'s in-degree rule).  **It must REFUSE something**, because the check is
#: that the storage is still ASSERTED from inside the inlined copy and not merely that
#: nothing raised: a validator that resolved the reference to an empty schema would
#: accept ``{"nope": ...}`` as happily as it accepts ``{"word": ...}``.
#:
#: An OBJECT and not a constrained scalar, for a reason about the fixture rather than
#: about the defect: D2 lowers a constrained scalar to a named alias in the run-wide
#: ``constraints`` module, which a two-document run does not write (``emit.write``'s
#: ``package`` gate), so the emitted module would import a symbol no tree holds.  This
#: shape lowers to a nested class in the emitted module itself.
SHARED = {
    "type": "object",
    "properties": {"word": {"type": "string"}},
    "required": ["word"],
    "additionalProperties": False,
}

#: The REFERENCED document, stating its own root ``$id`` the way every document of bundle
#: 3.3 and of upstream's 3.2.4 artifact states one.  Its ``inner`` property is the second
#: occurrence of :data:`SHARED`, and it is the occurrence that ends up UNDER the ``$id``.
INNER = {
    "$id": f"{BASE}core/inner.json",
    "title": "Inner Like",
    "type": "object",
    "properties": {"inner": SHARED},
    "additionalProperties": False,
}

#: The REFERRING document, whose record is the one that breaks: the inlined copy of
#: ``core/inner.json`` arrives with its ``$id``, and the hoisted ``#/definitions/Shared0``
#: written at ``/properties/held/properties/inner`` then resolves against the COPY.
OUTER = {
    "$id": f"{BASE}core/outer.json",
    "title": "Outer Like",
    "type": "object",
    "properties": {"held": {"$ref": f"{BASE}core/inner.json"}, "also": SHARED},
    "additionalProperties": False,
}


def write_bundle(tmp_path: Path, documents: dict[str, dict]) -> Path:
    """A bundle directory holding exactly ``documents``.

    ``$schema`` first and the document's own keys after, so a document stating its own
    ``$id`` states it where the published bundles state it.
    """
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root


@contextlib.contextmanager
def emitted(at: Path, out: emit.Emitted, module: str) -> Iterator[object]:
    """``out`` written as a tree, BOUND IN FRONT as a run binds one, and ``module`` imported.

    ``tests/test_applied_schema.py``'s ``_bound_in_front``, for its reason: an emitted
    module imports by ABSOLUTE name, so the modules have to be imported under the records
    package's own name and cannot be loaded from a path -- and a class resolves its record
    from the tree it was loaded from (``_base._record_root``,
    ``adcp-client-python-ir3l``), which is what makes ``strict_validate`` here read THIS
    record rather than the committed tree's.  Undone on the way out, with the modules it
    bound dropped, so no later test inherits the binding.

    **THE BINDING REACHES EVERY PACKAGE LEVEL, NOT ONLY THE ROOT, and that is
    ``adcp-client-python-ca70``.**  Binding ``at`` on the records package alone decides
    ``core.outer`` only while ``adcp.types._schemas.core`` is UNBOUND: once any earlier
    reader has imported the real subpackage it sits in ``sys.modules`` with the real
    tree's ``__path__``, ``core.outer`` is looked up along that list alone, and the module
    just written is unreachable -- ``ModuleNotFoundError``.  Measured: green alone and
    beside ``tests/test_the_second_bundle.py``, red beside ``tests/test_approximation.py``,
    ``tests/test_the_domain_surface.py`` and ``tests/test_the_alias_layer_is_names.py``,
    at ``-n 0``, deterministically.  **So the clause was green by arriving first**, which
    is the one way a gate reports the schedule rather than the tree.

    Each level of ``module``'s dotted name therefore gets the matching subdirectory of
    ``at`` in FRONT of its own ``__path__``, whether that level is already bound or is
    loaded here, and each insertion is undone in reverse on the way out.

    **AND THE TREE THE LEAF CAME FROM IS ASSERTED**, for ``tests/fresh.py``'s reason at
    its own ``_bound()``: a binding that reaches nothing does not disagree with the checks
    below, it hands them the COMMITTED record and they pass against an artifact this
    bundle did not produce.  A reader that cannot fail is green, so the read is graded
    here rather than hoped for.
    """
    emit.write(out, at, None)
    package = importlib.import_module(_base.PACKAGE)
    before = set(sys.modules)
    parts = module.split(".")
    bound: list[tuple[object, str]] = []
    try:
        for level in range(len(parts)):
            # ``level`` 0 is the records package itself; each later one is the subpackage
            # that holds the next name, imported through the binding already in place so
            # a level written into ``at`` resolves there.
            here = at.joinpath(*parts[:level])
            at_level = (
                package
                if level == 0
                else importlib.import_module(f"{_base.PACKAGE}." + ".".join(parts[:level]))
            )
            at_level.__path__.insert(0, str(here))
            bound.append((at_level, str(here)))
            importlib.invalidate_caches()
        leaf = importlib.import_module(f"{_base.PACKAGE}.{module}")
        assert str(getattr(leaf, "__file__", "")).startswith(str(at)), (
            f"{leaf.__name__} resolved to {getattr(leaf, '__file__', None)}, which is not "
            f"under the tree this check wrote ({at}): the binding did not reach the module "
            "and every assertion below would have graded another tree's record"
        )
        yield leaf
    finally:
        for at_level, here in reversed(bound):
            at_level.__path__.remove(here)
        for name in sorted(set(sys.modules) - before):
            del sys.modules[name]
        importlib.invalidate_caches()


def test_a_hoisted_storage_reference_resolves_from_inside_an_inlined_copy_stating_an_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """THE REPRODUCTION, through the SHIPPED entry point and in miniature.

    Two documents, one repeated subtree and one stated ``$id`` -- which is the whole of
    the live shape: ``core/frequency-cap-constraints.json`` references
    ``core/frequency-cap-impression-constraints.json``, the copy arrives with its ``$id``,
    and ``#/definitions/Shared2`` is written under it.  Here the storage entry is
    ``Shared0``.

    **Three payloads and not one.**  The first is one both documents ACCEPT, and before the
    repair ``strict_validate`` answered it with ``PointerToNowhere`` rather than with a
    verdict.  The second and third are refused BY THE STORED SUBTREE, one at each
    occurrence -- the one under the inlined copy's ``$id`` and the one outside it -- so a
    validator that resolved the reference to nothing, or to an empty schema, fails here as
    well.  That is what makes this a check on the storage being ASSERTED and not on a raise
    having stopped.

    **THE NETWORK IS REMOVED rather than mocked at the resolver.**  An ``$id`` is an
    absolute URI, and a resolver re-pointed at one could legitimately try to FETCH it --
    ``jsonschema`` deprecates that path, says it "will shortly become an error", and it was
    measured at 4.4 s per validation against a live URL.  Anything reaching for it here has
    to open a socket, and this one raises on construction.
    """
    root = write_bundle(tmp_path, {"core/outer.json": OUTER, "core/inner.json": INNER})
    out = emit.emit(root, ["core/outer.json"])
    assert out.refusals == {}, out.refusals
    assert sorted(out.emitted) == ["core/inner.json", "core/outer.json"], out.emitted

    # THE SHAPE IS THE LIVE ONE, asserted before the payloads so a green answer cannot
    # come from a record that happens to hoist nothing: the entry exists, and it is
    # referenced from the position INSIDE the inlined copy -- which is where the copy's
    # own ``$id`` re-based everything under it.
    carried = json.loads(out.files["core/outer.json"])
    entries = claimed(
        "the storage entries of the referring record", bundle.section_entries(carried)
    )
    under_the_copy = carried["properties"]["held"]["properties"]["inner"]
    assert "$ref" in under_the_copy, (under_the_copy, sorted(entries))
    assert under_the_copy["$ref"].lstrip("#") in entries, (under_the_copy, sorted(entries))

    class Refuses(socket.socket):
        def __init__(self, *a: object, **k: object) -> None:
            raise AssertionError("the validator opened a socket")

    monkeypatch.setattr(socket, "socket", Refuses)
    with emitted(tmp_path / "tree", out, "core.outer") as module:
        model = module.OuterLike
        accepted = {"held": {"inner": {"word": "w"}}, "also": {"word": "w"}}
        assert model.strict_validate(accepted), accepted
        for payload, where in (
            ({"held": {"inner": {"nope": "w"}}, "also": {"word": "w"}}, "under the inlined copy"),
            ({"held": {"inner": {"word": "w"}}, "also": {"nope": "w"}}, "outside it"),
        ):
            with pytest.raises(Exception) as raised:  # noqa: B017 -- the TYPE is the assertion
                model.strict_validate(payload)
            assert isinstance(raised.value, jsonschema.ValidationError | ValueError), (
                f"the storage reference {where} did not refuse a value the stored subtree "
                f"refuses; it reported {type(raised.value).__name__}: {raised.value}"
            )
            assert "word" in str(raised.value), (
                f"refused {where}, but not on the stored subtree's own keywords: {raised.value}"
            )


def test_no_record_of_the_second_bundle_states_an_id_below_its_root() -> None:
    """THE RULE over a real population: one record, one ``$id``, and it is the document's.

    Bundle 3.3 is the only committed bundle that states a ``$id`` at all, and it states
    one at every portable document root -- so its records are where an inlined copy's
    identifier can be read.  Over the 733 portable documents that state a cross-document
    reference (the ones where any copying happens), **730 carried a ``$id`` below their
    root before the repair**, every one of them another document's.

    Read off ``bundle.nodes``, which is ``recorded``'s OWN descent (``bundle.subschemas``,
    the table's descent column), so the walk that finds a stated ``$id`` and the walk that
    drops one cannot come to disagree about what a schema position is.  That is also what
    keeps this clause clear of ``extensions/extension-meta.json``'s ``properties`` entry,
    which the check below is about.

    The root's own ``$id`` is asserted KEPT and asserted to be the one the DOCUMENT states
    -- not merely present -- because a record that lost it would state nothing about where
    the document it is lives, and a record that invented one would be worse.
    """
    population = sorted(bundle.portable(SECOND))
    known = set(population)
    referring = claimed(
        "portable documents of bundle 3.3 stating a cross-document reference",
        [
            document
            for document in population
            if any(
                bundle.split_ref(uri)[0]
                for _, uri, _ in bundle.references(bundle.read(SECOND, document))
            )
        ],
        inside=population,
    )
    ratchet(
        "bundle 3.3 documents whose record inlines a copy",
        len(referring),
        at_least=700,
        because="the population is the bundle's own reference graph; it moves when the "
        "bundle does, and a collapse to a handful would make the clause below vacuous",
    )
    below_the_root: dict[str, list[tuple[str, object]]] = {}
    wrong_root: dict[str, tuple[object, object]] = {}
    for document in sorted(referring):
        record = bundle.record(SECOND, document, known)
        if isinstance(record, Refusal):
            continue  # a refused document emits nothing and carries no record
        found = [
            (pointer, node["$id"])
            for pointer, node in bundle.nodes(record)
            if pointer and "$id" in node
        ]
        if found:
            below_the_root[document] = found[:3]
        stated = bundle.read(SECOND, document).get("$id")
        if record.get("$id") != stated:
            wrong_root[document] = (stated, record.get("$id"))
    assert below_the_root == {}, (
        f"{len(below_the_root)} of {len(referring)} records of bundle 3.3 state a $id "
        f"below their root. draft-07 reads one as a new base URI for everything under it, "
        f"so a hoisted #/definitions/SharedN written under it resolves against the copy "
        f"instead of against the record root holding the section: {below_the_root}"
    )
    assert wrong_root == {}, (
        f"{len(wrong_root)} records state a root $id that is not the one their document "
        f"states, as (document's, record's): {wrong_root}"
    )


def test_a_properties_entry_named_id_survives_the_record() -> None:
    """``adcp-client-python-xvk3``'s defect, graded so this repair cannot recreate it.

    A ``$id`` is dropped where a node STATES one and never where a node is KEYED by one.
    The two are indistinguishable to a predicate reading the key's spelling, and the
    vendor transform behind ``schemas/cache/3.2`` read the spelling: it deleted
    ``extensions/extension-meta.json``'s ``properties.$id`` entry, leaving the document
    ``required``-ing a property it declares no schema for, and the emitted field carries
    ``Any`` where the document states a pattern.

    Bundle 3.3 still states the entry, so the fact is gradable on a committed bundle: the
    document's ``properties`` hold ``$id`` with its ``pattern``, and the record holds the
    same subschema at the same pointer.
    """
    document = "extensions/extension-meta.json"
    known = set(claimed("bundle 3.3 portable documents", bundle.portable(SECOND)))
    assert document in known, sorted(k for k in known if "extension" in k)
    raw = bundle.read(SECOND, document)
    entry = raw["properties"]["$id"]
    assert "pattern" in entry, entry
    assert "$id" in raw.get("required", []), raw.get("required")

    record = bundle.record(SECOND, document, known)
    assert not isinstance(record, Refusal), record
    held = bundle.expanded(record, record)
    assert isinstance(held, dict), held
    assert held["properties"].get("$id") == entry, (
        "the record dropped or rewrote a properties ENTRY named $id, which is a "
        "constraint on an instance and not an identifier: "
        f"{held['properties'].get('$id')!r} against the document's {entry!r}"
    )
