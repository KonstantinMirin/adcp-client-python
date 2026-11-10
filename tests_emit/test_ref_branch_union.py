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

import fresh
import pytest
from compiled import compiled
from nodeset import claimed, partitions
from pydantic import ValidationError

from adcp.types._base import BranchDispatchMixin
from codegen import bundle, compiler, emit
from codegen.lower import composition
from codegen.lower import union as lower_union
from codegen.refusal import Kind

REPO = Path(__file__).resolve().parents[1]
#: **The bundle a run reads, taken from the ONE declaration of it**
#: (``adcp-client-python-lzzj.11.1``).  This module held its own PUBLISHED literal while
#: every class it grades was emitted from the PATCHED bundle, so its two halves ranged over
#: two different document sets.  Measured against ``fresh.PUBLISHED``: the published
#: directory is portable over 1,054 documents and the run's over 1,059, the five only the
#: patched one holds are documents ``patches/8525`` ADDS, and of the 1,054 they share 211
#: differ -- 200 of those beyond ``$schema``/``title``/``description``.  So the published
#: path is ``adcp-client-python-fr4r``'s lookup error waiting at whichever clause names a
#: document first, and a quietly different answer at each of the others.
BUNDLE = fresh.BUNDLE

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

    Five properties, and each one is a thing a wrong implementation gets wrong:

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
    * and a payload comes back as the arm its ``kind`` names, which is the dispatch doing
      the work rather than a union trying each branch.
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

    **THE INDEX IS §4's FIFTH CANDIDATE AND NOT ITS FOURTH, so a bare ``$ref`` branch
    reaches it only where the TARGET names nothing.**  This asserted
    ``AnimalBranch0``/``AnimalBranch1`` of all three fixtures, which was right while the
    index was the candidate after ``required``.  :data:`names.REF_TARGET_CANDIDATE` sits between
    them now -- "where the branch is a bare ``$ref``, the TARGET's own derived name" --
    and a bare ``$ref`` branch ALWAYS has a target, so for these three fixtures candidate 4
    answers and the index is never reached: ``Cat`` and ``Dog`` say something
    ``Animal`` does not, so the branches are ``AnimalCat`` and ``AnimalDog``.

    So the fixtures grade the CANDIDATE LIST and the index keeps a fixture of its own, which is
    the one structure that reaches candidate 5 through a ``$ref`` branch: a target whose derived
    name says nothing the ROOT's does not (``names._distinguishing`` answers ``""``).
    ``AnimalKind`` over a target titled ``Animal`` is that case, and the second branch's
    ``Zebra`` is candidate 4 beside it -- the two candidates meeting in one module, which is what
    this test claimed before and now has a fixture that can show.

    Four fixtures, because "no shared distinct const" has three shapes -- no pin at all,
    a pin only one branch carries, and one pin repeated -- and the index has a fourth of
    its own.  That all three of the first land on candidate 4 and the fourth falls past it to
    the index is what says the dispatch stopped standing in front of §4's naming rules.

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
    #: The one ``$ref``-branch shape that reaches the INDEX: the first target's derived
    #: name is a leading run of the root's own, so candidate 4 has no distinguishing remainder
    #: to spell and answers nothing; the second target's does, so it keeps candidate 4.
    index_root = {**_ROOT, "title": "Animal Kind"}
    index_targets = {
        "cat.json": {**unpinned["cat.json"], "title": "Animal"},
        "dog.json": {**unpinned["dog.json"], "title": "Zebra"},
    }
    # **Candidate 4 for all three**, from three different places on the candidate list: the first
    # fixture reaches it because candidates 1-3 answer nothing, the second because only one
    # branch has a pin (that one takes candidate 2, which spells the same chain here), and the
    # third from a COLLISION -- candidate 2 derives one name for both, so neither is
    # identified and both fall.
    for targets, want in ((unpinned, ["AnimalCat", "AnimalDog"]),
                          (one_sided, ["AnimalCat", "AnimalDog"]),
                          (repeated, ["AnimalCat", "AnimalDog"])):
        at = _fixture(_ROOT, targets)
        try:
            out = emit.emit(at, ["root.json"])
            assert not out.refusals, out.refusals
            assert "root.json" in out.emitted, out.emitted
            text = out.files["root.py"]
            for name in want:
                assert f"class {name}(Animal, " in text, (name, text)
            # **THE THIRD FIXTURE EMITS, and §4 is what changed** (candidate 2 collides so
            # both branches FALL, 2026-10-29; ``adcp-client-python-10l.78``).  It refused
            # here on the collision rule with a hand-minted VERDICT: both branches pin
            # ``pet``, both derived ``AnimalPet``, and both chains were one segment with
            # nothing to lengthen by.  §4 reads that as the candidate having failed to identify
            # either branch rather than as the document's own fault -- "two nodes of this
            # document derive one class name" is a fact about ``lower/names.py``.
            #
            # The name the collision produced appears NOWHERE: it identified neither
            # branch, so it is not a name either of them keeps.
            assert "AnimalPet" not in text, text
        finally:
            shutil.rmtree(at)

    at = _fixture(index_root, index_targets)
    try:
        out = emit.emit(at, ["root.json"])
        assert not out.refusals, out.refusals
        assert "root.json" in out.emitted, out.emitted
        text = out.files["root.py"]
        # Candidate 5 and candidate 4 in one module, each named: the first branch's target says
        # nothing the root's name does not, the second's does.
        assert "class AnimalKindBranch0(AnimalKind, Animal):" in text, text
        assert "class AnimalKindZebra(AnimalKind, Zebra):" in text, text
        # And the index is a FALLBACK and not a default: the branch that could be named
        # is not named by its position.
        assert "AnimalKindBranch1" not in text, text
    finally:
        shutil.rmtree(at)


def test_a_ref_branch_whose_target_is_not_a_class_refuses_by_name() -> None:
    """A base has to be a class: §4 "What becomes what" makes a scalar root an
    ``Annotated`` alias, and subclassing one is a ``TypeError`` at import -- so it is
    refused by name rather than
    emitted as a module nobody can import.  The same refusal
    ``lower.composition.lower_composition`` raises for a ``$ref`` conjunct, at the one other
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
    """The row's REAL population, named, and the verdict each one reaches.

    Claimed from the bundle rather than listed, so a fourteenth appearing upstream lands
    here, and PARTITIONED by whether the branch list is reached at all: four of the
    THIRTEEN carry a root ``allOf`` or ``properties``, which is a conjunction with every
    branch that no pointer addresses (``ROOT_CONJUNCTS``), so they refuse before any
    branch is planned and this row never sees them.  The other NINE are the row's own
    population.

    **IT WAS ELEVEN AND SEVEN, AND THE TWO THAT ARRIVED ARE THE PATCH SET'S**
    (``adcp-client-python-lzzj.11.1``).  This module read the published bundle while the
    classes it grades were emitted from the patched one; moved onto the run's own bundle,
    ``core/geo-place-system.json`` and ``core/geo-place-type.json`` join the population,
    because ``patches/8525`` rewrites each one's ``/anyOf/1`` from
    ``{"type": "string", "format": "uri", "pattern": "^https://"}`` to a bare
    ``$ref`` on ``core/https-url.json`` -- which is what "a union root with a bare ``$ref``
    branch" names.  Pure GROWTH, measured in both directions: 11 roots against 13, the
    original seven all still planned, nothing left.  Re-derived rather than re-pasted
    (``a-frozen-set-can-be-the-only-thing-stopping-a-loop-from-running``), and the loop the
    pin was standing in front of is re-derived with it below.

    What is asserted of each is the property this row is responsible for -- that no
    refusal anywhere in the run still reads "a bare $ref branch has no node to declare a
    subclass from" -- and, now, the verdict: ALL NINE EMIT.

    **The second emitter arrives at ``adcp-client-python-10l.55``:**
    ``core/assets/asset-union.json``, whose ``/oneOf/3`` branch references the UNION root
    ``core/assets/vast-asset.json``.  The branch row refused it for not being a class --
    the gate asked whether the target had a ``compiler.Shape`` and a union base's does not
    cross a module boundary -- and ``compiler.TargetKind`` tells the two questions apart,
    so §4's branch rule applies: the target supplies the fields and the union's base
    supplies the dispatch.

    The retired sentence is asserted absent over the WHOLE refusal set and not over
    these thirteen, because four further documents reached it through a CHAIN and a check
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
                    __import__("codegen.intersect", fromlist=["x"]).declaring(
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
        # The two ``patches/8525`` adds to this population, by rewriting ``/anyOf/1`` from
        # a ``pattern``ed URI string to a bare ``$ref`` on ``core/https-url.json``.
        "core/geo-place-system.json",
        "core/geo-place-type.json",
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

    # ``core/assets/asset-union.json`` is the second emitter, at
    # ``adcp-client-python-10l.55``: a ``$ref`` branch onto a UNION root is §4's two bases
    # like any other, once the gate asks ``compiler.TargetKind`` instead of asking whether
    # the target has a ``compiler.Shape``.
    # ``core/media-buy-available-action-id.json`` is the first, and it does not emit
    # through this row: its other branch declares ``type: "string"``, so the DOCUMENT says
    # its instance is a scalar and §4 "What becomes what" makes the root an ``Annotated``
    # alias with no branch classes and no dispatch at all (``states_a_scalar_instance``).
    # The row's own description predicted it would REFUSE for want of a discriminant; it
    # was already emitting, by the alias path, at the trunk this row branched from.
    assert "core/media-buy-available-action-id.json" in out.emitted
    # **ALL NINE EMIT, STATED -- and the form this replaces was a loop that could not
    # fail.**  It read ``for document in roots - before_the_branches: if document in
    # out.emitted: continue; assert out.refusals[document]["keyword"] and [...]["pointer"]``
    # beside a comment saying "each of the seven still refuses but TWO".  Measured when
    # ``adcp-client-python-lzzj.11.1`` moved this module onto the run's own bundle: all
    # nine emit, and all SEVEN emitted on the published bundle too -- so the body never ran
    # at the trunk this re-derivation branched from either, and the sentence beside it had
    # been wrong for longer than the pin above was stale.  The emitted count this row moves
    # is not ZERO and has not been.  A loop whose every member hits ``continue`` is the
    # dead gate ``a-frozen-set-can-be-the-only-thing-stopping-a-loop-from-running``
    # measured, so the fact is asserted instead of iterated: a root that stops emitting
    # lands here by NAME, which is what the skipped loop could not do.
    refusing = sorted(document for document in roots - before_the_branches if document not in out.emitted)
    assert refusing == [], (
        "a ref-branch union root that emits today stopped emitting, so this clause's own "
        "sentence and the pinned population above are both out of date about it; re-measure "
        f"before re-pinning: { {d: out.refusals.get(d) for d in refusing} }"
    )


# --------------------------------------------------------------------------- #
# §5's base-list rule: the dispatch mixin where no base already carries it
# --------------------------------------------------------------------------- #
def test_the_dispatch_mixin_is_named_only_where_no_base_already_carries_it() -> None:
    """§5: "The suppression is a function of the BASE LIST and not of the route that
    reached it" (decided 2026-10-29).

    ``BranchDispatchMixin`` has to come FIRST so the MRO finds its
    ``__get_pydantic_core_schema__``, and a union base already carries it -- so naming it
    beside such a base puts a class before its own subclass and Python refuses to build
    the module. :func:`lower.composition.dispatching_bases` is the one reading, asked at the point
    the list is built, so both routes into ``lower_union`` get it: the one that carries
    :class:`lower_union.Enclosing` and the DISPATCH, which does not.

    Asserted on the FUNCTION in both directions and TRANSITIVELY, because a branch class
    of a union carries the mixin two hops up and asking only the immediate list would name
    it again.
    """
    mod = compiler.Module(document="probe.json")
    plain = composition.dispatching_bases((), mod)
    assert [b.path for b in plain] == ["BranchDispatchMixin"], plain
    assert (compiler.ir.BASE_MODULE, "BranchDispatchMixin") in mod.imports, (
        "the import is added where the name is, so a suppressed mixin imports nothing"
    )
    # A base that IS the mixin: not named twice.
    assert composition.dispatching_bases(plain, mod) == plain
    # A base this module declares whose own bases carry it -- the union base, and then a
    # class descending from that base, which is the transitive hop.
    mod.declarations.append(
        compiler.ir.ClassDecl(name="", ref=None, fields=(), bases=plain)
    )
    base = compiler.ir.TypeRef("", local=True)
    assert [b.path for b in composition.dispatching_bases((base,), mod)] == [""], (
        "a union base already carries the mixin"
    )
    mod.declarations.append(
        compiler.ir.ClassDecl(name="/anyOf/0", ref=None, fields=(), bases=(base,))
    )
    branch = compiler.ir.TypeRef("/anyOf/0", local=True)
    assert [b.path for b in composition.dispatching_bases((branch,), mod)] == ["/anyOf/0"], (
        "and so does a class that descends from one, two hops up"
    )
    # A base this module does NOT declare is not followed and the mixin is named, which is
    # the conservative direction: an imported symbol has no declaration here to read.
    outside = compiler.ir.TypeRef("SomeImportedClass", local=True)
    assert [b.path for b in composition.dispatching_bases((outside,), mod)] == [
        "BranchDispatchMixin",
        "SomeImportedClass",
    ]


def test_the_nested_union_base_of_postal_area_imports_and_dispatches() -> None:
    """``core/postal-area.json``, and the check is an IMPORT rather than a reading of
    the emitted text.

    Its ``/anyOf/0`` is a branch of the root union that composes a ``$ref`` whose target
    is a union ROOT, so §5's ``$ref`` row distributes the target's branches and the branch
    class becomes a union base of its own -- reached through
    ``lower.composition.lower_composition``, not through the branch loop that builds
    :class:`lower_union.Enclosing`. With the mixin named unconditionally there the module
    was ``(BranchDispatchMixin, PostalArea, AdCPBaseModel)``: an inconsistent MRO, and the
    module did not import.

    **The module had been emitting for some time and nothing could see it**, because it
    was not in the committed tree, so no instrument imported it. That is why this test
    EXECUTES the emitted text instead of asserting on its shape: a base list that reads
    plausibly and does not build is exactly the defect that hid here.
    """
    out = emit.emit(BUNDLE, ["core/postal-area.json"])
    assert "core/postal-area.json" in out.emitted, out.refusals
    assert (
        "class PostalAreaCountrySystemValues(PostalArea, AdCPBaseModel):"
        in out.files["core/postal_area.py"]
    ), out.files["core/postal_area.py"]
    # **The CLOSURE, written as a real package and IMPORTED.**  Not ``exec`` of the one
    # module's text: its relative imports are what reach the distributed target's branch
    # classes, and an MRO is built when the class statement runs, so the check has to run
    # every statement the module writer produced in the package layout it wrote them for.
    # The committed tree does not carry this document yet, which is the whole reason the
    # defect hid, so the package is a temporary one rooted at its own name.
    at = Path(tempfile.mkdtemp())
    package = f"probe_{at.name}"
    try:
        emit.write(out, at / package, at)
        sys.path.insert(0, str(at))
        module = importlib.import_module(f"{package}.core.postal_area")
        root, nested = module.PostalArea, module.PostalAreaCountrySystemValues
        assert issubclass(nested, root)
        # The mixin is INHERITED, which is the half that says suppressing it loses
        # nothing: the nested base still carries the hook and still holds its own branch
        # list, so a payload reaching the outer arm dispatches again inside it.
        assert issubclass(nested, BranchDispatchMixin)
        assert len(nested._branch_models) > 1, nested._branch_models
        assert len(root._branch_models) > 1, root._branch_models
    finally:
        if str(at) in sys.path:
            sys.path.remove(str(at))
        for name in [m for m in sys.modules if m.startswith(package)]:
            del sys.modules[name]
        shutil.rmtree(at)
