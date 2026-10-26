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
        resolved = bundle.resolved(at, "root.json")
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


def test_a_ref_branch_root_with_no_derivable_dispatch_defers_and_never_verdicts() -> None:
    """The refusal kind, which is the half of this row that is an accounting fact.

    A root whose branches own no fields and pin no shared distinct ``const`` matches
    NEITHER of §4's two dispatch sources.  §4's second source is a key the bundle's
    manifest states, which is ``salesagent-j3k2l.60``'s row -- so the obstruction is
    UNWRITTEN CODE and the kind is a DEFERRAL.  A verdict there counts a clearable
    document as finally refused, which is what this row found and corrected: the bare
    ``$ref`` branch refused as a verdict, and ten documents -- six roots and four
    reached through them -- were accounted for as finally refused while the code to
    clear them was simply not written.

    Three fixtures, because "no shared distinct const" has three shapes and a refusal
    that cannot tell them apart is not actionable: no pin at all, a pin only one branch
    carries, and one pin repeated.
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
    for targets in (unpinned, one_sided, repeated):
        at = _fixture(_ROOT, targets)
        try:
            out = emit.emit(at, ["root.json"])
            # The TARGETS emit -- they are reached through the ``$ref`` and each one is
            # an ordinary object root.  It is the union ROOT that refuses.
            assert "root.json" not in out.emitted, out.emitted
            row = out.refusals["root.json"]
            assert row["keyword"] == "oneOf", row
            assert row["pointer"] == "/", row
            assert row["kind"] is Kind.DEFERRED, row
            assert row["resolved"] is Kind.DEFERRED, row
            # The pins themselves are in the sentence, which is what makes the three
            # shapes tellable apart without re-running the emitter.
            assert "salesagent-j3k2l.60" in row["detail"], row
            assert ("pins" in row["detail"]) or ("pin" in row["detail"]), row
        finally:
            shutil.rmtree(at)


def test_a_ref_branch_whose_target_is_not_a_class_refuses_by_name() -> None:
    """A base has to be a class: §4 "What becomes what" makes a scalar root an
    ``Annotated`` alias, and subclassing one is a ``TypeError`` at import -- so it is
    refused by name rather than
    emitted as a module nobody can import.  The same refusal
    ``compiler.lower_composition`` raises for a ``$ref`` conjunct, at the one other
    position a reference becomes a base.
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
    subclass from" -- and the property it is NOT: six of the seven still refuse, through
    a target of their own that another row's gap blocks, so the emitted count this row
    moves is ZERO and the constructed pair above is where the mechanism is graded.

    The retired sentence is asserted absent over the WHOLE refusal set and not over
    these eleven, because four further documents reached it through a CHAIN and a check
    over the roots alone would not see them.
    """
    population = sorted(bundle.portable(BUNDLE))
    out = emit.emit(BUNDLE, population)
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

    # Each of the seven still refuses but one, and every refusal is on something OTHER
    # than this row's ground: five through a target of their own, one on a nested
    # union's ``discriminator`` sibling (``salesagent-j3k2l.67``).  Asserted as "refused, by name and pointer"
    # rather than pinned to a keyword, because which gap each waits on is the other
    # rows' fact and moves when they land.
    # ``core/media-buy-available-action-id.json`` is the ONE of the seven that emits,
    # and it does not emit through this row: its other branch declares
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
