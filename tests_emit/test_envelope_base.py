"""The drifted envelope family: one base 26 documents share, and what it may not claim.

``codegen/lower/envelope.py`` carries the design.  What is graded here is the four things
that make the base safe, each in both directions:

* the family is DERIVED from the bundle and its membership test is the SHAPE, so a 27th
  envelope joins without an edit and a node that stops stating the shape leaves;
* the base is NOT A PAIR -- §8 never grades it -- and every member class still is;
* a member's own acceptance is untouched, measured on the two documents that disagree;
* the base's annotations are a SUPERTYPE of every member's own, so programming against it
  cannot be wrong about a member.

The row is an ERGONOMICS row: it moves no figure of the report, which is asserted here
rather than claimed.
"""

from __future__ import annotations

import functools
import importlib
import pkgutil

import fresh
import jsonschema
import pytest
from compiled import compiled

from adcp.types._base import SchemaBound, schema_at
from adcp.types._schemas.core.error import Error
from adcp.types.envelopes import FailedResponse
from codegen import bundle, emit, keywords
from codegen.lower import envelope
from nodeset import claimed, partitions

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

#: **The family, as the set of nodes and not as a count of them.**  Measured on bundle
#: 3.2 and read back off ``bundle.envelopes`` -- so this is the DERIVATION's answer
#: written down, and not the input to it: nothing in ``codegen/`` holds this list, and a
#: 27th envelope reddens this one line rather than passing unnoticed.  A SET and not a
#: count for ``tests/nodeset``'s own reason: a count is one bundle version's reading of a
#: quantity, and two rows in flight compute two different correct values for it.
MEMBERS = frozenset(
    {
        "account/get-account-financials-response.json#/oneOf/1",
        "account/sync-accounts-response.json#/oneOf/1",
        "account/sync-governance-response.json#/oneOf/1",
        "brand/acquire-rights-response.json#/oneOf/3",
        "brand/creative-approval-response.json#/oneOf/3",
        "brand/get-brand-identity-response.json#/oneOf/1",
        "brand/get-rights-response.json#/oneOf/1",
        "brand/search-brands-response.json#/oneOf/1",
        "brand/update-rights-response.json#/oneOf/1",
        "brand/verify-brand-claim-response.json#/oneOf/1",
        "brand/verify-brand-claims-response.json#/oneOf/1",
        "content-standards/calibrate-content-response.json#/oneOf/1",
        "content-standards/get-content-standards-response.json#/oneOf/1",
        "content-standards/get-media-buy-artifacts-response.json#/oneOf/1",
        "content-standards/list-content-standards-response.json#/oneOf/1",
        "content-standards/validate-content-delivery-response.json#/oneOf/1",
        "creative/sync-creatives-response.json#/oneOf/1",
        "media-buy/build-creative-response.json#/oneOf/4",
        "media-buy/create-media-buy-response.json#/oneOf/1",
        "media-buy/log-event-response.json#/oneOf/1",
        "media-buy/provide-performance-feedback-response.json#/oneOf/1",
        "media-buy/sync-audiences-response.json#/oneOf/1",
        "media-buy/sync-catalogs-response.json#/oneOf/1",
        "media-buy/sync-event-sources-response.json#/oneOf/1",
        "media-buy/update-media-buy-response.json#/oneOf/1",
        "signals/activate-signal-response.json#/oneOf/1",
    }
)

#: **``WAITING`` STOOD HERE AND HAS REACHED EMPTY** (2026-11-04,
#: ``adcp-client-python-99m``).  It named the members whose DOCUMENT did not emit yet, so
#: there was no class for the base to reach, and its own comment said what to do when
#: that stopped being true: "when one of those steps lands, the member's class takes the
#: base with no change here but this set, which is why it is a set and not a tolerance."
#: Every one of §14 steps 9 and 10's documents emits now -- ``./check`` reports
#: ``refused 0`` -- so the set shrank to nothing, which is a ratchet reaching its floor
#: and not a gate being relaxed.
#:
#: It had grown to ten entries and the two checks reading it asserted it as an EQUALITY,
#: so the shrink reddened them both rather than passing.  What they say now is the TOTAL
#: form the set was always a deduction from: every member of the derived family has a
#: class, and that class takes the base.  A member whose document stops emitting reddens
#: by NAME against that, which is strictly more than re-pinning a smaller set would say.


@functools.cache
def family() -> tuple[tuple[bundle.Envelope, dict], ...]:
    return bundle.envelopes(BUNDLE)


@functools.cache
def whole() -> emit.Emitted:
    """One run over the whole portable population, shared by the three tests that read
    a figure off it.  ``functools.cache`` and not a fixture, because the result is a pure
    function of the bundle and the emitter and a run costs a minute and a half."""
    return compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))


@functools.cache
def classes() -> dict[bundle.Envelope, type]:
    """Every class the emitted tree carries, keyed by the node its reference names.

    Read as a consumer reads it -- off ``__adcp_schema__`` -- so the key is the one the
    family is keyed by and the two cannot come to disagree about which node a class is.
    """
    import adcp.types._schemas as pkg

    out: dict[bundle.Envelope, type] = {}
    for info in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        module = importlib.import_module(info.name)
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, SchemaBound)
                and "__adcp_schema__" in value.__dict__
                and value.__module__ == info.name
            ):
                ref = value.__adcp_schema__
                out[bundle.Envelope(ref.document, ref.pointer.lstrip("#"))] = value
    return out


def test_the_family_is_derived_from_the_bundle_and_its_test_is_the_shape() -> None:
    """The set is a function of the bundle, and membership is two facts about one node.

    **Not a hand-written list of documents**, which is the defect §4 names for branch
    discrimination: such a list is complete with respect to itself, so a 27th envelope
    added upstream leaves it silently wrong in both directions.  So the SITES are asserted
    by name -- a measurement, which is allowed to move with the bundle -- and the
    PREDICATE is asserted to be the thing that produced them: feeding each member's own
    node back through ``is_an_envelope`` answers yes, and perturbing either of the two
    facts answers no.
    """
    members = family()
    sites = claimed(
        "nodes of the drifted envelope family",
        (f"{site.document}#{site.pointer}" for site, _ in members),
    )
    assert sites == MEMBERS, sorted(sites ^ MEMBERS)
    # Every one is a BRANCH of a root union, which is what makes the base's position
    # among a member class's bases a question at all (§4 puts the union's base first).
    assert {site.pointer.split("/")[1] for site, _ in members} == {"oneOf"}, sorted(
        {site.pointer for site, _ in members}
    )
    # Every member is a member by the predicate, and the predicate is what selected it.
    for site, node in members:
        assert bundle.is_an_envelope(node), site
    # And the predicate is not vacuous in either of its two facts.  Perturbed on a real
    # member's node rather than on a fixture, so what is graded is the node the bundle
    # states.
    _, one = members[0]
    assert not bundle.is_an_envelope({**one, "required": ["errors", "context"]})
    assert not bundle.is_an_envelope(
        {**one, "properties": {k: v for k, v in one["properties"].items() if k != "ext"}}
    )
    assert not bundle.is_an_envelope({**one, "properties": {**one["properties"], "x": {}}})
    assert not bundle.is_an_envelope({k: v for k, v in one.items() if k != "required"})
    # A document path is not among the facts: a member stripped of its title and
    # description is still a member, which is what "the shape, not the name" means.
    assert bundle.is_an_envelope(
        {k: v for k, v in one.items() if k not in ("title", "description")}
    )


def test_the_familys_documents_do_not_share_an_accepted_set() -> None:
    """The measurement the base is SHAPED BY: a base claiming authority would be wrong.

    ``errors`` is the drifted property.  Read on the bundle: ``minItems: 1`` at 21 members
    and absent at 5, every one of the 5 under ``content-standards/``.  Read on an
    INSTANCE, through the branch node §8 pairs a member class with: one member refuses an
    empty ``errors`` and another accepts it.  Both halves, because the first is a fact
    about the documents and the second is the fact that matters.
    """
    members = family()
    tight = {
        site.document
        for site, node in members
        if node["properties"]["errors"].get("minItems") == 1
    }
    loose = {site.document for site, _ in members} - tight
    assert len(tight) == 21 and len(loose) == 5, (sorted(tight), sorted(loose))
    assert {d.split("/")[0] for d in loose} == {"content-standards"}, sorted(loose)

    # On an instance, against the document -- not against the model, which is the half
    # §2 says is not the authority.  The payload carries ``status`` because the branch
    # node is read under the root's own siblings (§8), and both arms take the same one.
    payload = {"errors": [], "status": "completed"}
    refuses = ("brand/creative-approval-response.json", "#/oneOf/3")
    accepts = ("content-standards/calibrate-content-response.json", "#/oneOf/1")
    for (document, pointer), expected in ((refuses, False), (accepts, True)):
        at = next(s for s, _ in members if (s.document, s.pointer) == (document, pointer.lstrip("#")))
        node = bundle.node_at(bundle.read(BUNDLE, document), at.pointer)
        assert bundle.is_an_envelope(node), at
        model = classes()[at]
        assert jsonschema.Draft7Validator(schema_at(model.__adcp_schema__)).is_valid(
            payload
        ) is expected, (at, payload)


def test_the_base_is_not_a_pair_and_every_member_class_still_is() -> None:
    """§8 never grades the base, on three counts, and grades every member as before.

    The pairing is ``issubclass(value, SchemaBound) and "__adcp_schema__" in
    value.__dict__``, over the modules of ``adcp.types._schemas``
    (``tests/test_emit.py``'s ``graded``).  The base fails it three times -- it declares
    no ``__adcp_schema__``, it is not a ``SchemaBound`` at all, and it is not in that
    package -- and any one alone would be enough.  All three are asserted, because a
    later row that moves one of them must still find the others.
    """
    assert "__adcp_schema__" not in FailedResponse.__dict__
    assert not hasattr(FailedResponse, "__adcp_schema__")
    assert not issubclass(FailedResponse, SchemaBound)
    assert not FailedResponse.__module__.startswith("adcp.types._schemas"), (
        FailedResponse.__module__
    )
    # And the base states no policy of its own, which is the half the three emitted
    # members of the LOOSE group measured: pydantic merges a base's ``model_config`` into
    # its subclass's, so a base carrying §2's ``extra: ignore`` would impose it on every
    # member whose own node states no ``additionalProperties``.
    assert FailedResponse.model_config == {}, FailedResponse.model_config
    # And the consequence a consumer meets: the base is not an authority on anything.
    with pytest.raises(AttributeError):
        FailedResponse.strict_validate({"errors": []})

    # The members are unchanged pairs: each declares its own reference, and the reference
    # is its own node's and not the base's.
    taken = {site: model for site, model in classes().items() if site in dict(family())}
    # ``MEMBERS`` whole, and no longer ``MEMBERS - WAITING``: every member's document
    # emits, so every member has a class and the deduction has nothing left to subtract.
    assert {f"{s.document}#{s.pointer}" for s in taken} == MEMBERS, sorted(taken)
    for site, model in taken.items():
        assert "__adcp_schema__" in model.__dict__, site
        assert model.__adcp_schema__.document == site.document
        assert model.__adcp_schema__.pointer == f"#{site.pointer}"
        # And the member's ``extra`` policy is still its own document's.  Where the
        # branch node states ``additionalProperties`` the class states it; where it does
        # not, §5 says the root's own compiles onto the union's base and every branch
        # inherits it -- so the member's policy is its union base's, and a base appended
        # after it must not have replaced that.  This is the assertion that caught the
        # loose group when the base was an ``AdCPBaseModel``.
        stated = bundle.node_at(bundle.read(BUNDLE, site.document), site.pointer).get(
            "additionalProperties"
        )
        inherited = model.__bases__[0].model_config["extra"]
        assert model.model_config["extra"] == ("allow" if stated else inherited), site


def test_every_member_class_takes_the_base_and_no_other_class_does() -> None:
    """The equality in both directions: the classes with the base are exactly the members.

    One direction says the pass reached every member the tree carries; the other says it
    reached nothing else.  A membership test checked one way is complete with respect to
    itself, which is the reason §8's own equalities have two directions.

    **AND IT IS TOTAL OVER THE FAMILY NOW** (2026-11-04).  Eleven of the 26 members were
    in documents that did not emit, so they had no class to take the base, and this check
    subtracted a named ``WAITING`` set from both sides.  Those documents emit --
    ``./check`` reports ``refused 0`` -- so the subtraction is gone and the third
    direction is stated instead: every member of the DERIVED family has a class at all.
    That is the direction the deduction was hiding, and it is the one a regression would
    come back through: a member whose document stops emitting used to be absorbed by
    editing a set, and now reddens by name.
    """
    members = dict(family())
    carried = {
        site
        for site, model in classes().items()
        if any(b is FailedResponse for b in model.__mro__[1:])
    }
    present = {site for site in members if site in classes()}
    assert carried == present, sorted(carried ^ present)
    # THE THIRD DIRECTION: every member of the family has a class.  Without this the two
    # above are complete with respect to a tree that emitted no member at all.
    missing = sorted(
        f"{site.document}#{site.pointer}" for site in set(members) - present
    )
    assert missing == [], (
        f"{len(missing)} member(s) of the derived family have no class, so the base "
        f"cannot reach them: {missing}.  Every such document used to be one the run "
        "REFUSES, which is what the retired WAITING set absorbed; at refused 0 a member "
        "without a class means the pass missed one."
    )


def test_the_base_annotates_a_supertype_of_every_members_own_field() -> None:
    """What a consumer may rely on: the base's types admit what a member's own types do.

    The base's ``errors`` is ``list[Error]`` and a member's is its own -- ``Error`` at 25
    of the 26 and a SUBCLASS of it at ``media-buy/sync-catalogs-response.json``, whose
    ``items`` composes the reference rather than stating it bare.  That is why the shape
    rule takes a descent PREFIX: a member may say more about a property than the family
    agrees on, and §2's ``allOf`` row makes saying more a subclass.  Asserted through
    ``issubclass`` rather than reasoned about.

    What a consumer may NOT rely on is asserted beside it: the base states no bound on
    ``errors``, so a payload the base's annotation admits is not thereby one any document
    accepts -- the concrete class's ``strict_validate`` is what decides that.
    """
    assert FailedResponse.model_fields["errors"].annotation == list[Error]
    assert not FailedResponse.model_fields["errors"].metadata, "the base states a bound"
    members = dict(family())
    taken = {site: model for site, model in classes().items() if site in members}
    claimed("member classes the tree carries", taken)
    for site, model in taken.items():
        element = model.model_fields["errors"].annotation.__args__[0]
        assert issubclass(element, Error), (site, element)
        for key in ("context", "ext"):
            assert (
                model.model_fields[key].annotation
                == FailedResponse.model_fields[key].annotation
            ), (site, key)
    # The one member whose element is a strict subclass, named so the prefix rule has a
    # case rather than a claim.
    composing = next(
        site for site in taken if site.document == "media-buy/sync-catalogs-response.json"
    )
    assert taken[composing].model_fields["errors"].annotation.__args__[0] is not Error


def test_the_base_shape_is_derived_and_states_nothing_the_family_disagrees_on() -> None:
    """``bundle.envelope_shape``'s answer, by name, and the drift it leaves out.

    Three properties, each with the descent path and the document the rule derived.  The
    keys the members do not state alike -- ``minItems``, every ``description``, the one
    conditional refinement -- are not in the answer and so are not in the base, which is
    the row's whole statement about what the base can and cannot promise.
    """
    shape = bundle.envelope_shape(family(), bundle.portable(BUNDLE))
    assert shape == (
        bundle.Agreed("errors", True, (keywords.Position.ELEM,), "core/error.json"),
        bundle.Agreed("context", False, (), "core/context.json"),
        bundle.Agreed("ext", False, (), "core/ext.json"),
    ), shape
    # The ORDER is the family's own and not this test's: every member states the three in
    # that order, which is what lets a base declare one order at all.
    assert {tuple(node["properties"]) for _, node in family()} == {
        tuple(one.key for one in shape)
    }
    # And the drift is really absent from the base: the two facts the members disagree on
    # are stated by some member and by no field of the base.
    assert any(
        node["properties"]["errors"].get("minItems") for _, node in family()
    ), "no member states minItems, so the base dropping it proves nothing"
    assert FailedResponse.model_json_schema()["properties"]["errors"].get("minItems") is None


def test_the_base_module_is_a_function_of_the_bundle_and_not_of_the_run() -> None:
    """§9's one-document property, for the artifact a member's class imports.

    ``constraints.py`` beside it is a function of the RUN -- it holds the shapes a run
    resolved -- and this is not: the family is read off the bundle, so a run over one
    member writes the same base as a run over the whole population, and the member's own
    module is therefore the same text too.  Both halves asserted, because the second is
    what a consumer's import resolves against.
    """
    document = "brand/creative-approval-response.json"
    rel = emit.module_file(document, fresh.PACKAGES) + ".py"
    alone = compiled(BUNDLE, [document])
    # Against the WHOLE-POPULATION run's own output, read off the tree a fresh run wrote
    # (``docs/plan/architecture.md``, 2026-10-29, and ``tests/fresh.py``): comparing a
    # one-document run with a second whole-bundle run here would cost a second emission
    # to prove a property the materialised one already carries.  It used to read the
    # COMMITTED artifact, which made this one-document property conditional on when
    # ``src/`` was last regenerated.
    assert alone.beside["envelopes.py"] == (fresh.PACKAGE / "envelopes.py").read_text()
    assert alone.files[rel] == (fresh.TREE / rel).read_text()
    assert f"from {envelope.MODULE} import {envelope.BASE}" in alone.files[rel]


def test_the_row_moves_none_of_the_three_figures() -> None:
    """An ergonomics row: emitted, refused and approximated are the base's own numbers.

    Pinned as the SETS they are counts of and not as the counts, which is §8's rule for
    the verdict column: a figure arriving is attributable and a figure arriving for a new
    reason reddens.  So this asserts that no document of the family moved between emitting
    and refusing because of the base, and that the family declares no approximation --
    which is the design's claim that nothing is dropped.

    **THE FIRST ASSERTION REQUIRED A REFUSAL AND IS GONE** (2026-11-04).  It read

        assert documents & set(out.emitted) and documents & set(out.refusals)

    -- both halves non-empty -- which made a family with no refused document a FAILURE.
    At ``refused 0`` that is every family, and it is the state the row wanted: the claim
    is "the base costs no document its emission", so a refused half was evidence the
    design was being graded against, never evidence it needed.  What is asserted now is
    the claim itself, with the offenders NAMED -- and the accounting that was the second
    assertion survives as a partition, because "every family document is emitted or
    refused and never both" is still what makes the first meaningful.
    """
    out = whole()
    documents = {site.document for site, _ in family()}
    emitted, refused = documents & set(out.emitted), documents & set(out.refusals)
    # Total and disjoint over the family's documents: a document in neither is one the run
    # did not reach at all, which neither figure would report.
    partitions(documents, emitted=emitted, refused=refused)
    # **THE BASE COSTS NO DOCUMENT ITS EMISSION**, which is this row's whole claim about
    # the first two figures.  Named and not counted: a document refusing here is the base
    # having changed a verdict, and which document it is is the finding.
    assert sorted(refused) == [], sorted(refused)
    # Nothing is approximated FOR the family: every member keeps its own constraint, so
    # there is no widening to declare at any member's pointer.
    pointers = {f"{site.document}{site.pointer}" for site, _ in family()}
    declared = {
        f"{a.document}{a.pointer}"
        for one in out.approximations.values()
        for a in one
    }
    assert not (declared & pointers), sorted(declared & pointers)
