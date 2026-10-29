"""§4's ``$ref`` branch: a class with two bases, and a dispatch derived from the branches.

``salesagent-j3k2l.59``.  Two things this row decides and nothing else in the suite
grades, because **0 of the bundle's six ``$ref``-branch union roots emit today** -- every
one of them references at least one target that is itself refused, for reasons belonging
to other rows (a nested union's sibling, a root ``properties`` beside a union, a scalar
root used as an ``allOf`` base, a ``format`` on an array's items, a ``minItems``, a root
``allOf``).  A row whose population is empty is a derivation that passes vacuously, which
is the failure ``nodeset.claimed`` exists for -- so the mechanism is graded on a
CONSTRUCTED bundle driven through the real entry point, and the bundle's own six roots are
claimed by name beside it so that the day one of them clears, this file says what it must
then do.

**AND ONE CLEARED THROUGH THIS ROW AT ``adcp-client-python-10l.55``**:
``core/assets/asset-union.json``, whose ``/oneOf/3`` branch references the UNION root
``core/assets/vast-asset.json``.  The branch row refused it on "VASTAsset is not a class",
a question about :class:`compiler.Shape` reported as a statement about classes -- a union
root IS a class and its shape simply does not cross a module boundary -- and
:class:`compiler.TargetKind` tells the two apart.  So the derivation is no longer vacuous
on the real bundle, and the constructed pair below still grades the mechanism.

Every assertion below runs the production pipeline: ``emit.emit`` over a bundle directory,
``emit.write`` into a package, and then the written package is IMPORTED and asked to
validate -- so a rendering that does not run, a base order that breaks the MRO, or a
discriminator pydantic refuses is a failure here rather than a fact about the text.
"""

from __future__ import annotations

import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

from pydantic import ValidationError

from adcp.types._base import BranchDispatchMixin
from compiled import compiled
from codegen import bundle, compiler, emit, harness
from codegen.lower import union as lower_union
from codegen.refusal import Kind

from nodeset import claimed, partitions

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

#: One target document per branch, each pinning ``kind`` to its own value.  Object roots
#: with their own ``title``, because a bare ``$ref`` branch's SECOND base is the target's
#: class and a target with no class cannot be one.
_PINNED = {
    "cat.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Cat",
        "type": "object",
        "additionalProperties": False,
        "required": ["kind", "lives"],
        "properties": {
            "kind": {"type": "string", "const": "cat"},
            "lives": {"type": "integer"},
        },
    },
    "dog.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Dog",
        "type": "object",
        "additionalProperties": False,
        "required": ["kind", "breed"],
        "properties": {
            "kind": {"type": "string", "const": "dog"},
            "breed": {"type": "string"},
        },
    },
}

#: The root: two branches, each a BARE ``$ref``.  No ``discriminator`` keyword, because
#: §4 derives the dispatch from the branches and a declared keyword is read only where
#: they confirm it -- a root that emits without one is what proves the derivation is not
#: reading the keyword.
_ROOT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Animal",
    "type": "object",
    "oneOf": [{"$ref": "https://x/cat.json"}, {"$ref": "https://x/dog.json"}],
}


def _fixture(root: dict, targets: dict[str, dict]) -> Path:
    """A bundle directory holding ``root.json`` and its targets."""
    at = Path(tempfile.mkdtemp())
    (at / "root.json").write_text(json.dumps(root))
    for name, doc in targets.items():
        (at / name).write_text(json.dumps(doc))
    return at


def _imported(at: Path) -> tuple[Any, str]:
    """Emit the fixture bundle, write it as a package, import it, and return the root.

    The written package rather than the rendered text: a two-base class is exactly the
    shape that can render and not import -- an inconsistent MRO, a discriminated union
    pydantic refuses to build, a base that is an ``Annotated`` alias -- and none of those
    is visible in a string.
    """
    out = emit.emit(at, ["root.json"])
    assert not out.refusals, out.refusals
    package = at / "pkg"
    emit.write(out, package, None)
    sys.path.insert(0, str(at))
    try:
        for name in [n for n in sys.modules if n == "pkg" or n.startswith("pkg.")]:
            del sys.modules[name]
        module = importlib.import_module("pkg.root")
    finally:
        sys.path.remove(str(at))
    return module, out.files["root.py"]


def test_a_ref_branch_is_a_class_with_two_bases_and_the_dispatch_is_derived() -> None:
    """§4, the whole sentence: the target supplies the fields, the base the dispatch.

    Six properties, and each one is a thing a wrong implementation gets wrong:

    * the branch is a class of its own, named by §4 "Names"'s ``const`` choice off the
      pin it inherits --
      so the root exports one symbol and the arms are reachable from it;
    * its bases are the union's base AND the target, in that order, so
      ``isinstance(payload, Base)`` holds for the arm and the target's fields arrive by
      inheritance;
    * its ``__adcp_schema__`` names the BRANCH's own pointer and not the target's
      document, which is what gives the arm its own graded pair (P2: nothing of the
      target is copied);
    * the base carries the DERIVED discriminator, with no ``discriminator`` keyword in
      the document to read it from;
    * a payload comes back as the arm its ``kind`` names, which is the dispatch doing
      the work rather than a union trying each branch;
    * and the harness grades the branch against its own node.
    """
    at = _fixture(_ROOT, _PINNED)
    try:
        module, text = _imported(at)
        base = module.Animal
        assert issubclass(base, BranchDispatchMixin)
        assert base._BRANCH_DISCRIMINATOR == "kind", text
        assert base._branch_combinator() == "oneOf"

        branches = {b.__name__: b for b in base._branch_models}
        assert sorted(branches) == ["AnimalCat", "AnimalDog"], text
        for i, (name, want) in enumerate([("AnimalCat", "Cat"), ("AnimalDog", "Dog")]):
            arm = branches[name]
            # The two bases, in §4's order: the union's base FIRST.
            assert [b.__name__ for b in arm.__bases__] == ["Animal", want], arm.__bases__
            assert issubclass(arm, base)
            assert arm.__adcp_schema__.document == "root.json"
            assert arm.__adcp_schema__.pointer == f"#/oneOf/{i}"
            # The fields are the target's, by inheritance, and the arm declares none.
            assert set(arm.model_fields) == {"kind", *({"lives"} if i == 0 else {"breed"})}

        got = base.model_validate({"kind": "dog", "breed": "corgi"})
        assert type(got) is branches["AnimalDog"], type(got)
        assert isinstance(got, base)
        # ``Base(**data)`` too, which no core schema reaches: the mixin's ``__new__``
        # asks the base's own validator, so direct construction resolves to the arm.
        assert isinstance(base(kind="cat", lives=9), branches["AnimalCat"])

        # **The key alone selects the arm.**  A payload whose ``kind`` names one branch
        # and whose FIELDS are the other's is reported against THE ARM THE KEY NAMED, in
        # the document's own vocabulary -- which is the difference §4 names between a
        # discriminated union and one that tries each branch and reports one ``missing``
        # per field per branch.
        with pytest.raises(ValidationError) as caught:
            base.model_validate({"kind": "dog", "lives": 9})
        kinds = {(e["type"], e["loc"]) for e in caught.value.errors()}
        assert kinds == {("missing", ("dog", "breed")), ("extra_forbidden", ("dog", "lives"))}, kinds

        # And a key naming NO branch is the combinator, because the error pydantic raises
        # there is about the key rather than about a branch.
        with pytest.raises(ValidationError) as caught:
            base.model_validate({"kind": "emu"})
        assert [e["type"] for e in caught.value.errors()] == ["oneOf"], caught.value.errors()

        # **The graded pair**, built the way the tree's own pairs are: the SCHEMA half is
        # the node at the pointer the CLASS names, read out of the resolved document, so
        # a branch class that states a fact its own node does not is reported ``added``
        # and one that drops a fact its node states is reported ``missing``.  This is the
        # check the retired refusal's stated reason was about -- an inherited field being
        # unreportable at the branch's pointer -- and for a ``$ref`` branch it is not:
        # the resolved document carries the target's whole content AT that pointer.
        resolved = bundle.record(at, "root.json")
        for arm in base._branch_models:
            node = resolved
            for step in arm.__adcp_schema__.pointer.removeprefix("#").strip("/").split("/"):
                node = node[int(step)] if isinstance(node, list) else node[step]
            report = harness.compare_schema(node, arm, document=resolved)
            assert report.compared, (arm.__name__, "nothing compared", report)
            assert not report.missing, (arm.__name__, report.missing)
            assert not report.differs, (arm.__name__, report.differs)
            assert not report.added, (arm.__name__, report.added)
    finally:
        shutil.rmtree(at)


def test_a_ref_branch_root_with_no_derivable_dispatch_names_its_branches_by_index() -> None:
    """**The dispatch mints NO refusal at all now, which is §4's own answer written**
    (``adcp-client-python-10l.21``): "a union matching none of the three emits a plain
    ``A | B`` over its branches and declares an UNDERDETERMINED approximation at the
    union's pointer."

    This test was the accounting half of its row: a root whose branches own no fields
    and pin no shared distinct ``const`` matches none of §4's sources, and the kind it
    refused with had to be a DEFERRAL rather than a verdict, because a verdict counts a
    clearable document as finally refused.  The declaration answers that question
    differently and better -- there is no refusal to carry a kind -- so what is left to
    assert is that the dispatch is silent and each fixture reaches ITS OWN next outcome.

    **Two of the three now EMIT** (``adcp-client-python-10l.41``): §4's fourth branch
    rung names a branch with no identity by its INDEX, ``<Base>Branch<i>``, so a bare
    ``$ref`` branch with no title, no pin and no ``required`` of its own is named rather
    than refused.  The third still refuses, and on the OTHER naming mechanism: two
    branches pinning one ``const`` derive the SAME name, and both chains are one segment,
    so §4's collision rule has nothing to lengthen by.  That is the bundle's own
    ``trusted-match/provider-registration.json`` in a fixture, and
    ``adcp-client-python-10l.42`` is the row that owns it.

    Three fixtures, because "no shared distinct const" has three shapes: no pin at all,
    a pin only one branch carries, and one pin repeated.  That the first two emit and the
    third refuses on a DIFFERENT sentence is what says the dispatch stopped standing in
    front of §4's naming rules.

    ``tests/test_union_disjointness.py::
    test_a_root_whose_branches_overlap_declares_underdetermined_and_emits`` is where the
    declaration itself is graded, on a root whose branches CAN be named.
    """
    unpinned = {
        name: {**doc, "properties": {k: v for k, v in doc["properties"].items() if k != "kind"},
               "required": [r for r in doc["required"] if r != "kind"]}
        for name, doc in _PINNED.items()
    }
    one_sided = {"cat.json": _PINNED["cat.json"], "dog.json": unpinned["dog.json"]}
    repeated = {
        name: {**doc, "properties": {**doc["properties"], "kind": {"type": "string", "const": "pet"}}}
        for name, doc in _PINNED.items()
    }
    # Neither branch has an identity, so BOTH take §4's fourth rung; with one pin only
    # the pinned branch takes rung 2 and the other the index, which is the two rungs
    # meeting in one module.
    for targets, want in ((unpinned, ["AnimalBranch0", "AnimalBranch1"]),
                          (one_sided, ["AnimalBranch1", "AnimalCat"])):
        at = _fixture(_ROOT, targets)
        try:
            out = emit.emit(at, ["root.json"])
            assert not out.refusals, out.refusals
            text = out.files["root.py"]
            for name in want:
                assert f"class {name}(Animal, " in text, (name, text)
        finally:
            shutil.rmtree(at)

    at = _fixture(_ROOT, repeated)
    try:
        out = emit.emit(at, ["root.json"])
        # **THE THIRD FIXTURE EMITS NOW, and §4 is what changed** (rung 2 collides so both
        # branches FALL, 2026-10-29; ``adcp-client-python-10l.78``).  It refused here on
        # the collision rule with a hand-minted VERDICT: both branches pin ``pet``, both
        # derived ``AnimalPet``, and both chains were one segment with nothing to lengthen
        # by.  §4 reads that as the rung having failed to identify either branch rather
        # than as the document's own fault -- "two nodes of this document derive one class
        # name" is a fact about ``lower/names.py`` -- so both fall.
        #
        # They land on rung FOUR and not rung three, and the reason is this fixture's own
        # shape: a bare ``$ref`` branch states no ``required`` of its OWN (its target
        # does), so rung 3 answers nothing for it and the index is what is left.  That is
        # the same reading the first two fixtures above exercise, reached from a collision
        # instead of from an absence.
        assert not out.refusals, out.refusals
        assert "root.json" in out.emitted, out.emitted
        text = out.files["root.py"]
        for name in ("AnimalBranch0", "AnimalBranch1"):
            assert f"class {name}(Animal, " in text, (name, text)
        # The name the collision produced appears NOWHERE: it identified neither branch,
        # so it is not a name either of them keeps.
        assert "AnimalPet" not in text, text
    finally:
        shutil.rmtree(at)


def test_a_ref_branch_whose_target_is_not_a_class_refuses_by_name() -> None:
    """A base has to be a class: §4 "What becomes what" makes a scalar root an
    ``Annotated`` alias, and subclassing one is a ``TypeError`` at import -- so it is
    refused by name rather than
    emitted as a module nobody can import.  The same refusal
    ``compiler.lower_composition`` raises for a ``$ref`` conjunct, at the one other
    position a reference becomes a base.

    **THE SENTENCE IS ASSERTED, because this is the one of §4's three root outcomes the
    branch row still refuses** (``adcp-client-python-10l.55``).  The gate used to ask
    whether the target had a ``compiler.Shape`` and report the answer as "is not a
    class", which was true here and FALSE for a UNION root -- a class whose shape did
    not cross the module boundary.  It asks ``compiler.TargetKind`` now, so the only
    target that reaches this refusal is the alias, and the detail says alias:
    ``dog.json`` is a bare ``type: "string"`` root, which is this population's scalar
    document.
    """
    at = _fixture(
        _ROOT,
        {
            "cat.json": _PINNED["cat.json"],
            "dog.json": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Dog",
                "type": "string",
            },
        },
    )
    try:
        out = emit.emit(at, ["root.json"])
        assert "root.json" not in out.emitted, out.emitted
        row = out.refusals["root.json"]
        assert row["keyword"] == "$ref", row
        assert row["pointer"] == "/oneOf/1", row
        assert row["resolved"] is Kind.VERDICT, row
        assert "is not a class but an Annotated alias" in row["detail"], row
        assert "SCALAR root" in row["detail"], row
    finally:
        shutil.rmtree(at)


def test_the_bundles_ref_branch_roots_are_claimed_by_name_and_wait_on_their_targets() -> None:
    """The row's REAL population, named, and why none of it emits yet.

    Claimed from the bundle rather than listed, so a twelfth appearing upstream lands
    here, and PARTITIONED by whether the branch list is reached at all: four of the
    eleven carry a root ``allOf`` or ``properties``, which is a conjunction with every
    branch that no pointer addresses (``ROOT_CONJUNCTS``), so they refuse before any
    branch is planned and this row never sees them.  The other SEVEN are the row's own
    population and are the seven its description names.

    What is asserted of each is the property this row is responsible for -- that no
    refusal anywhere in the run still reads "a bare $ref branch has no node to declare a
    subclass from" -- and the property it is NOT: five of the seven still refuse, through
    a target of their own that another row's gap blocks, so the emitted count this row
    moves is ZERO and the constructed pair above is where the mechanism is graded.

    **The second emitter arrives at ``adcp-client-python-10l.55``:**
    ``core/assets/asset-union.json``, whose ``/oneOf/3`` branch references the UNION root
    ``core/assets/vast-asset.json``.  The branch row refused it for not being a class --
    the gate asked whether the target had a ``compiler.Shape`` and a union base's does not
    cross a module boundary -- and ``compiler.TargetKind`` tells the two questions apart,
    so §4's branch rule applies: the target supplies the fields and the union's base
    supplies the dispatch.

    The retired sentence is asserted absent over the WHOLE refusal set and not over
    these eleven, because four further documents reached it through a CHAIN and a check
    over the roots alone would not see them.
    """
    population = sorted(bundle.portable(BUNDLE))
    out = compiled(BUNDLE, population)
    roots = claimed(
        "union roots with a bare $ref branch",
        [
            document
            for document in population
            if (kw := lower_union.keyword(doc := bundle.read(BUNDLE, document)))
            and any(
                isinstance(branch, dict)
                and set(
                    __import__("codegen.compiler", fromlist=["x"]).declaring(
                        branch, __import__("codegen.keywords", fromlist=["x"]).Position.BRANCH
                    )
                )
                == {"$ref"}
                for branch in doc[kw]
            )
        ],
        inside=population,
    )
    before_the_branches = {
        document
        for document in roots
        if any(kw in bundle.read(BUNDLE, document) for kw in lower_union.ROOT_CONJUNCTS)
    }
    partitions(roots, planned=roots - before_the_branches, refused_at_the_root=before_the_branches)
    assert sorted(roots - before_the_branches) == [
        "compliance/task-completion-data.json",
        "core/assets/asset-union.json",
        "core/async-response-data.json",
        "core/media-buy-available-action-id.json",
        "core/pricing-option.json",
        "core/requirements/asset-requirements.json",
        "core/requirements/catalog-field-binding.json",
    ], sorted(roots - before_the_branches)
    assert sorted(before_the_branches) == [
        "creative/get-creative-features-response.json",
        "media-buy/decline-proposals-response.json",
        "media-buy/refine-proposals-response.json",
        "media-buy/request-proposals-response.json",
    ], sorted(before_the_branches)

    # Gone from every refusal in the run, chains included.
    for document, row in sorted(out.refusals.items()):
        assert "has no node to declare a subclass from" not in row["detail"], document

    # Each of the seven still refuses but TWO, and every refusal is on something OTHER
    # than this row's ground: four through a target of their own, one on a nested
    # union's ``discriminator`` sibling (``salesagent-j3k2l.67``).  Asserted as "refused, by name and pointer"
    # rather than pinned to a keyword, because which gap each waits on is the other
    # rows' fact and moves when they land.
    # ``core/assets/asset-union.json`` is the second emitter and it DOES emit through
    # this row, at ``adcp-client-python-10l.55``: a ``$ref`` branch onto a UNION root is
    # §4's two bases like any other, once the gate asks ``compiler.TargetKind`` instead
    # of asking whether the target has a ``compiler.Shape``.
    # ``core/media-buy-available-action-id.json`` is the first, and it does not emit
    # through this row: its other branch declares
    # ``type: "string"``, so the DOCUMENT says its instance is a scalar and §4 "What
    # becomes what" makes the root an ``Annotated`` alias with no branch classes
    # and no dispatch at all
    # (``states_a_scalar_instance``).  The row's own description predicted it would
    # REFUSE for want of a discriminant; it was already emitting, by the alias path, at
    # the trunk this row branched from.
    assert "core/media-buy-available-action-id.json" in out.emitted
    for document in roots - before_the_branches:
        if document in out.emitted:
            continue
        row = out.refusals[document]
        assert row["keyword"] and row["pointer"], document
