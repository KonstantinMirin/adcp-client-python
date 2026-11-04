"""A fact at a position with no field to carry it, and what section 5 does with each.

Three positions in this file, and they are one question asked three ways: a document
states a keyword at a node whose Python rendering has no slot for it, so either the
fact reaches the WRONG thing, or it is dropped in silence, or the walk refuses.

* a ``default`` on a REQUIRED property -- **dropped and reported** (section 5's
  ``default`` row).  Dropping it changes no accepted set: the key is in every instance
  the document admits, so the default can never be applied.  Reported because an
  emitter that discards a document's fact in silence is the one defect nothing else
  here catches.
* a ``format`` with no type selected, at an ELEM, a MAPV or a BRANCH -- **a named
  alias carries it** (section 5's ``format`` row).  On a FIELD it rides as
  ``json_schema_extra``; inside a container there is no field, and on a union branch
  the field holds the other branches too, so a bound written there refuses values the
  document accepts (section 2, "Constraints bind to the type, not the field").
* an array's or a mapping's own bound at a BRANCH -- **on the branch's own type, never
  on the field holding the union** (section 5's ``minItems``/``maxItems`` and
  ``minProperties``/``maxProperties`` rows).
* a ROOT ``required`` naming a key only the BRANCHES declare -- **recorded in
  ``_ROOT_REQUIRED``, with no field on the base** (section 5's ``required`` row at
  ROOT beside a union).  The branch classes hold the fields and their own requiredness
  is what refuses a payload omitting one; the base carries the names so the refusal is
  reported on the document's own ``required`` rather than on the combinator.

Every perturbation here is a PAIR of documents differing in the one key being judged,
so a passing arm and a failing arm are separated by the judged dimension and by
nothing else.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

import jsonschema
from compiled import compiled
from pydantic import ValidationError

from codegen import bundle, emit
from codegen.ir import MISSING
from tests.nodeset import claimed, partitions

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
DRAFT = "http://json-schema.org/draft-07/schema#"


def _write(tmp_path: Path, documents: dict[str, dict]) -> Path:
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root


def _defaulted(required: list[str]) -> dict:
    """One object root with a defaulted boolean property, required or not."""
    return {
        "title": "Probe",
        "type": "object",
        "properties": {"active": {"type": "boolean", "default": True}},
        "required": required,
    }


# --------------------------------------------------------------------------- #
# a default on a required property: dropped, and reported
# --------------------------------------------------------------------------- #
def test_a_default_is_dropped_where_the_property_is_required_and_kept_where_it_is_not(
    tmp_path,
) -> None:
    """The one distinction, run both ways on two documents differing in ``required``.

    The ``jsonschema`` lines are what make this a measurement rather than a
    restatement of the code: with the key required the document refuses the empty
    object, so no admitted instance omits the key and the default has no instance to
    apply to; without it the empty object is admitted and the default is the value the
    document then means.  That is why one is dropped and the other is rendered.
    """
    demanded, optional = _defaulted(["active"]), _defaulted([])
    assert not jsonschema.Draft7Validator(demanded).is_valid({})
    assert jsonschema.Draft7Validator(optional).is_valid({})

    out = emit.emit(_write(tmp_path / "a", {"core/probe.json": demanded}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    assert out.drops == {"core/probe.json": {"/properties/active": True}}, out.drops
    assert "    active: bool\n" in out.files["core/probe.py"], out.files["core/probe.py"]

    out = emit.emit(_write(tmp_path / "b", {"core/probe.json": optional}), ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    assert out.drops == {}, out.drops
    assert "    active: bool | None = True\n" in out.files["core/probe.py"], out.files[
        "core/probe.py"
    ]


def _stated_default(document: str, root: Any, sub: Any) -> Any:
    """The ``default`` a property's declaration states, THROUGH a local ``$ref``.

    Draft-07 replaces a ``$ref`` node with its target, so the target's ``default`` IS the
    referring node's -- which is ``adcp-client-python-10l.26``'s own sentence and what
    ``compiler.local_reference`` now carries (``compiler.Module.referred``).  So the
    derivation this check ranges over has to follow the same resolution, or the emitter
    reports a drop the derivation calls invented.

    The node's OWN ``default`` wins where it states one, which is the precedence §5's
    ``$ref`` row gives a ``description`` sibling and the same order ``lower.objects.fields``
    reads the two in.  ``MISSING`` where neither states one, so a ``default: null`` -- a
    legal JSON value, and in this bundle -- is not read as an absence.
    """
    if not isinstance(sub, dict):
        return MISSING
    if "default" in sub:
        return sub["default"]
    ref = sub.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#"):
        return MISSING
    target = dict(bundle.nodes(root)).get(ref[1:])
    return target["default"] if isinstance(target, dict) and "default" in target else MISSING


def _same_instance_below(node: dict, pointer: str) -> list[tuple[str, dict]]:
    """Every subschema reached from ``node`` by SAME-INSTANCE hops alone, with its
    pointer: the descent §2's intersection follows.

    ``oneOf``/``anyOf``/``allOf`` and nothing else, to any depth.  draft-07 holds each
    of those against the instance the node describes, so a statement the node makes
    about a key holds at every one of them -- which is what makes a chain of them one
    instance and a ``properties`` or ``items`` hop a different one.  ``if``/``then``
    are out for ``_base.SAME_INSTANCE_LIST``'s own reason read on this keyword: a
    ``then`` applies only where the condition holds, so it does not state that the key
    is required.
    """
    out: list[tuple[str, dict]] = []
    for word in ("oneOf", "anyOf", "allOf"):
        for i, branch in enumerate(node.get(word) or ()):
            if not isinstance(branch, dict):
                continue
            where = f"{pointer}/{word}/{i}"
            out.append((where, branch))
            out += _same_instance_below(branch, where)
    return out


def _defaults_on_required_properties() -> dict[tuple[str, str], Any]:
    """Every (document, pointer) in the bundle where a property's declaration states a
    ``default`` -- its own, or its local ``$ref`` target's -- and its enclosing object
    REQUIRES the key, against the VALUE that declaration states.

    One derivation and not two: the set the check ranges over and the value each site
    drops are the same reading of the same declaration, so a site cannot be enumerated
    by one rule and graded by another.

    Read off the documents rather than off the run, so the set this check ranges over
    is a property of the bundle and the emitter's own record is what gets compared to
    it.  One level of ``properties`` only: the drop is reported at the pointer
    ``lower.objects.fields`` is handed, and a nested object's own properties are reached
    through their own node at their own pointer, which this enumerates too by walking
    every node the bundle yields.

    **A union BRANCH is enumerated against its enclosing object's declarations too**,
    because §2's intersection rule is what ``lower.objects.fields`` hands the branch: a branch
    of a worded object inherits the object's ``properties`` and its ``required``, so a
    key the object requires and states a ``default`` on is required AND defaulted at the
    branch's own pointer -- the branch restating the key without a default does not
    withdraw either fact.  Reached first by
    ``formats/canonical/seller_rendered_stateful_display.json``
    (``adcp-client-python-10l.50``), whose ``/properties/transitions/items`` requires
    ``transition_mode`` and defaults it to ``instant`` while all six of its branches
    restate the key: the run reports the drop at the object's pointer and at each
    branch's, which is seven sites for one stated fact.

    **THE TWO HALVES OF THE SHAPE MAY SIT AT TWO DIFFERENT POINTERS, and the descent is
    what reaches that.**  §2's intersection is followed as far as the pointer goes, so
    the ``default`` may be the enclosing object's while the ``required`` is a branch's
    OWN -- and then the key is required and defaulted at the branch, which is exactly
    what ``lower.objects.fields`` is handed there.  Two readings this had and now does not:
    it descended ONE combinator hop, so a branch of a branch was outside the
    enumeration; and it asked the enclosing node's ``required`` before looking at any
    branch at all, so a default the object states WITHOUT requiring was never carried
    down.  ``media-buy/proposal-refinement.json`` is both at once -- its root states
    ``change_kind`` with ``default: "amendment"`` and requires only ``proposal_id``,
    while ``/oneOf/1/anyOf/6`` requires ``change_kind`` -- and the run reported the drop
    there against an enumeration that did not hold the site.

    :func:`_same_instance_below` is the descent, and it is the SAME-INSTANCE hops only:
    a ``properties`` or an ``items`` hop moves to another instance and its node is
    enumerated on its own by the walk above.
    """
    found: dict[tuple[str, str], Any] = {}
    for document in bundle.portable(BUNDLE):
        root = bundle.read(BUNDLE, document)
        for pointer, node in bundle.nodes(root):
            props = node.get("properties") if isinstance(node, dict) else None
            if not isinstance(props, dict):
                continue
            demanded = node.get("required") if isinstance(node, dict) else None
            demanded = demanded if isinstance(demanded, list) else []
            for key, sub in props.items():
                stated = _stated_default(document, root, sub)
                if stated is MISSING:
                    continue
                here = key in demanded
                if here:
                    found[(document, f"{pointer}/properties/{key}")] = stated
                # §2's intersection at every same-instance descendant of this object,
                # which is where the same fact is handed to a second declaration.  The
                # branch's own ``default`` wins where it states one, which is the
                # precedence the intersection gives every keyword the two declarations
                # share -- and the requiredness holds where EITHER view states it, which
                # is the union §2's intersection spells for that keyword.
                for where, branch in _same_instance_below(node, pointer):
                    own = (branch.get("properties") or {}).get(key)
                    theirs = _stated_default(document, root, own)
                    wanted = branch.get("required")
                    if not here and key not in (wanted if isinstance(wanted, list) else []):
                        continue
                    found[(document, f"{where}/properties/{key}")] = (
                        stated if theirs is MISSING else theirs
                    )
    return found


def test_every_drop_the_run_reports_is_a_default_on_a_property_its_document_requires()\
        -> None:
    """The reported drops are exactly the shape section 5's row names, over the whole
    portable set, and the set is not empty.

    Both directions matter and only one of them is obvious.  A drop the bundle does
    not state at that shape would be the emitter discarding something else under this
    row's name; and the DOCUMENTS with the shape that this run never reached are
    reported as their own part rather than left in a difference of two totals, because
    a document refused on another row's keyword never reaches ``lower.objects.fields`` at
    all and its default is neither dropped nor rendered.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    reported = claimed(
        "drops the run reported",
        {(d, p) for d, sites in out.drops.items() for p in sites},
    )
    stated_by = _defaults_on_required_properties()
    stated = claimed("defaults the bundle states on a required property",
                     stated_by, inside=None)
    assert reported <= stated, sorted(reported - stated)
    partitions(stated, reported=reported, never_reached=stated - reported)
    for document, pointer in sorted(reported):
        assert out.drops[document][pointer] == stated_by[(document, pointer)], (
            document,
            pointer,
        )


# --------------------------------------------------------------------------- #
# the documents this row's renderings release, by name
# --------------------------------------------------------------------------- #
#: The documents that refused on one of this row's five causes and now EMIT, by name
#: rather than as a count: section 8's rule is that a check names the set it ranges
#: over, and a total says nothing about which documents moved.  Each is listed at the
#: cause it refused on; the ones that clear their cause and refuse FURTHER ON are
#: :data:`STILL_REFUSED`, which is this row's work done and not this row's failure.
RELEASED: dict[str, tuple[str, ...]] = {
    "a default on a required property": (
        "core/account.json",
        "core/reporting-delivery-config-state.json",
        "core/reporting-delivery-config.json",
    ),
    "a format inside a container": (
        "core/requirements/html-asset-requirements.json",
        "core/requirements/javascript-asset-requirements.json",
        "core/requirements/url-asset-requirements.json",
    ),
    "a format on a union branch": ("core/macro-bearing-url.json",),
    "an array bound on a union branch": (
        "governance/reported-outcome-error.json",
        "media-buy/get-media-buy-delivery-request.json",
        "media-buy/get-media-buys-request.json",
    ),
    # Decided by section 5's minProperties/maxProperties row, owned by
    # salesagent-j3k2l.70, and cleared by the same carrier: a mapping's own key count
    # at a MAPV is the same question as an array's bound at a BRANCH.
    "a mapping bound inside a container": (
        "trusted-match/publisher-targeting-kv-config.json",
        "trusted-match/publisher-tmpx-config.json",
    ),
}

#: The documents this row cleared whose NEXT refusal is another row's keyword, with
#: that keyword.  Named so that a later row clearing one of these moves a name out of
#: this map rather than changing a number -- and so that a document whose FIRST
#: refusal came back is read here as a regression rather than as a count going up.
#: **RE-MEASURED at ``adcp-client-python-10l.20``**, where one entry moved and none left:
#: ``core/media-buy.json`` was ``allOf`` at ``/properties/health/allOf/0``, whose target
#: ``MediaBuyHealth`` is not a class -- §5's ``$ref`` row at CONJ, which step 9 writes --
#: and it is now ``$ref`` at ``/properties/budget_allocation/allOf/0``, a CHAIN through
#: ``core/budget-allocation.json``.  The document got FURTHER and named its next
#: obstruction, which is the direction this map is pinned for.
#:
#: **TWO ENTRIES LEFT AT ``adcp-client-python-10l.21``, which is the SHRINK this map is
#: pinned for.**  ``account/list-accounts-response.json`` and
#: ``core/account-with-authorization.json`` both chained through
#: ``core/account-authorization.json``, whose ``#/properties/field_scopes
#: /additionalProperties`` carries a ``uniqueItems`` at a mapping value -- §5(b)'s row,
#: which this row's second instalment lands as a DECLARED WIDENING rather than a verdict.
#: All three emit.
#: **THREE MORE ENTRIES LEFT AT ``adcp-client-python-10l.21``'s FIFTH INSTALMENT, and
#: it is the same shrink.**  ``core/assets/pixel-tracker-asset.json`` and
#: ``core/assets/url-asset.json`` were both sitting on ``additionalProperties`` at
#: ``/properties/macro_declarations/items/allOf/1/properties/location`` -- a conjunct
#: restating a property ``core/macro-declaration.json`` declares -- which §5's
#: ``properties`` row at CONJ composes per key now, and
#: ``core/product-card-reference-asset.json`` chained behind the first of them.  All
#: three emit.
#: **ONE ENTRY LEFT AT ``adcp-client-python-10l.45``, and it is the same shrink.**
#: ``governance/get-plan-audit-logs-response.json`` chained through
#: ``core/attestation-reference.json``, whose
#: ``/properties/embedded_credential/properties/value`` is a ``type`` LIST with a
#: constraint on one arm -- a shape no check could read, so the row refused the document
#: rather than emit a node no check grades.  ``harness._type_list`` reads a union of arms
#: back as the ``type`` list it spells plus the per-arm facts, so a declaration at such a
#: node is provable and both documents emit.
#: **EMPTY at ``adcp-client-python-10l.109``, and the entry that left is below rather
#: than deleted** -- which is the whole of what this map is pinned for, taken to its end.
#: ``core/media-buy.json`` was the last one and it EMITS; the assertion that caught it
#: said so in as many words ("now emits: move it out of STILL_REFUSED") and could not run,
#: because this file was one of the seven failures the down gate was hiding.
STILL_REFUSED: dict[str, str] = {}

#: The documents that LEFT :data:`STILL_REFUSED` because a later row cleared their next
#: obstruction, with the keyword they were last refused on.  **A named set and not a
#: deletion**, for the reason the map above exists: a document whose refusal comes BACK is
#: a regression, and a count going from one to zero cannot say which document it was.  So
#: the two maps partition this row's whole handoff and each half is asserted in its own
#: direction -- this one EMITS, that one still refuses on the named keyword.
#:
#: ``core/media-buy.json``'s own history is the direction read twice: ``10l.20`` moved it
#: from ``allOf`` at ``/properties/health/allOf/0`` to ``$ref`` at
#: ``/properties/budget_allocation/allOf/0``, a chain through
#: ``core/budget-allocation.json``, and that chain now resolves.
CLEARED_BY_A_LATER_ROW: dict[str, str] = {
    "core/media-buy.json": "$ref",
}


def test_every_document_this_row_releases_emits_and_the_rest_name_their_next_keyword()\
        -> None:
    """The named sets, over a fresh whole-population run.

    A total would be satisfied by any twelve documents.  This asserts the twelve the
    row owns and the ones it cleared a refusal for without finishing, which is what a
    later re-derivation of the ownership can be checked against.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    released = claimed(
        "documents this row releases",
        {d for names in RELEASED.values() for d in names},
        inside=bundle.portable(BUNDLE),
    )
    assert released <= set(out.emitted), sorted(released - set(out.emitted))
    # The HANDOFF: every document this row cleared a refusal for without finishing,
    # whether it still refuses or has since been released.  Claimed as one set so the
    # denominator cannot go empty by a row emptying one half of it -- which is exactly
    # what happened to ``STILL_REFUSED``.
    handoff = claimed(
        "documents this row cleared a refusal for without finishing",
        set(STILL_REFUSED) | set(CLEARED_BY_A_LATER_ROW),
        inside=bundle.portable(BUNDLE),
    )
    assert handoff.isdisjoint(released), sorted(handoff & released)
    assert set(STILL_REFUSED).isdisjoint(CLEARED_BY_A_LATER_ROW), sorted(
        set(STILL_REFUSED) & set(CLEARED_BY_A_LATER_ROW)
    )
    for document, keyword in sorted(STILL_REFUSED.items()):
        row = out.refusals.get(document)
        assert row is not None, f"{document} now emits: move it to CLEARED_BY_A_LATER_ROW"
        assert row["keyword"] == keyword, (document, row)
    for document, was in sorted(CLEARED_BY_A_LATER_ROW.items()):
        row = out.refusals.get(document)
        assert row is None, (
            f"{document} refuses again on {row and row['keyword']!r}, having been cleared "
            f"of {was!r}: a refusal coming back is a regression and not a count going up"
        )


# --------------------------------------------------------------------------- #
# the facts reach the model, which is what a named carrier is for
# --------------------------------------------------------------------------- #
def test_a_format_inside_a_container_reaches_the_models_own_schema() -> None:
    """The element's ``format`` is in the rendered schema, read off
    ``model_json_schema()`` -- which is the whole point of naming the type rather than
    dropping it.

    Asserted against the emitted CLASS and not against the module text: a name in the
    text proves the alias was referenced, and this proves the alias carries the fact.
    """
    from adcp.types._schemas.core.requirements import url_asset_requirements as mod

    rendered = mod.URLAssetRequirements.model_json_schema()["properties"]["allowed_domains"]
    array = next(b for b in rendered["anyOf"] if b.get("type") == "array")
    assert array["items"] == {"type": "string", "format": "hostname"}, rendered
    assert mod.URLAssetRequirements.model_validate({"allowed_domains": ["a.example.com"]})


def test_an_array_bound_on_a_branch_binds_that_branch_and_not_the_field() -> None:
    """The row's correctness motive, asserted on the accepted set.

    ``{"minItems": 1}`` sits on ONE branch of ``status_filter``'s union.  Written onto
    the field holding the union it would bind the enum branch too, so the field would
    refuse a single status the document accepts -- the added direction.  On the
    branch's own type the document's own set comes back: a bare status, a non-empty
    list, and no empty list.
    """
    from adcp.types._schemas.media_buy.get_media_buys_request import GetMediaBuysRequest as R

    assert R.model_validate({"status_filter": "active"}).status_filter == "active"
    both = R.model_validate({"status_filter": ["active", "paused"]}).status_filter
    assert [s.value for s in both] == ["active", "paused"], both
    try:
        R.model_validate({"status_filter": []})
    except Exception:  # the type is pydantic's and the claim is refusal
        pass
    else:
        raise AssertionError("the empty list was accepted: the branch lost its minItems")
    rendered = R.model_json_schema()["properties"]["status_filter"]
    array = next(b for b in rendered["anyOf"] if b.get("type") == "array")
    assert array["minItems"] == 1, rendered
    assert "minItems" not in rendered, "the bound reached the field holding the union"


def test_a_stores_extra_key_type_is_enforced_although_pydantic_renders_none() -> None:
    """A ``propertyNames`` the model does not RENDER is still ENFORCED, measured.

    The class carries the document's key bound in the key type of its
    ``__pydantic_extra__``, and pydantic renders nothing for it -- so the enforcement
    cannot be read off the rendered schema and is graded on the ACCEPTED SET instead: a
    key one character past the document's ``maxLength: 128`` is refused and a short one
    is accepted, and the rendered schema really does carry no ``propertyNames``.
    """
    from adcp.types._schemas.governance.reported_outcome_error import ReportedOutcomeError as R

    bound = bundle.read(BUNDLE, "governance/reported-outcome-error.json")["propertyNames"]
    # The KEYWORD is asserted and the VALUE is read, not restated: the bound is one
    # document's number and a copy of it here would be a second place to go stale.
    assert sorted(bound) == ["maxLength"], bound
    assert "propertyNames" not in R.model_json_schema(), "pydantic renders it after all"
    assert R.model_validate({"k": "v"}).model_extra == {"k": "v"}
    try:
        R.model_validate({"k" * (bound["maxLength"] + 1): "v"})
    except Exception:  # the type is pydantic's and the claim is refusal
        return
    raise AssertionError("a key past the document's bound was accepted")


# --------------------------------------------------------------------------- #
# a ROOT required naming a key only the branches declare
# --------------------------------------------------------------------------- #
def _union_root(required: list[str]) -> dict:
    """One union root whose branches declare two keys the root's properties do not.

    The shape ``core/product-format-declaration.json`` states at ``/``: a
    discriminated ``oneOf`` whose every branch declares AND requires ``kind`` and
    ``value``, beside a root ``properties`` that declares neither.  ``required`` is the
    judged key and the only difference between the two arms.
    """
    def branch(tag: str, word: str) -> dict:
        return {
            "title": f"Probe {tag.upper()}",
            "properties": {"kind": {"const": tag}, "value": {"type": word}},
            "required": ["kind", "value"],
        }

    return {
        "title": "Probe",
        "type": "object",
        "properties": {"label": {"type": "string"}},
        "required": required,
        "oneOf": [branch("a", "string"), branch("b", "integer")],
    }


def _emitted_model(document: str, out: emit.Emitted) -> Any:
    """The emitted module's root symbol, EXECUTED rather than inspected.

    A constructed document is not in the shipped package, so the text is run into a
    namespace of its own -- the same reading ``test_emit._constructed`` takes, and for
    its reason: a test that inspects the text passes on a rendering that does not run,
    and this row's claim is about an accepted set.  The relative import lines are
    dropped because the sibling modules do not exist here; this document references
    nothing, so nothing is pre-bound.
    """
    text = out.files[document.replace(".json", ".py")]
    module = types.ModuleType("_inner_facts_union_fixture")
    sys.modules[module.__name__] = module
    try:
        exec(  # executing the compiler's own output is the point
            "\n".join(x for x in text.splitlines() if not x.startswith("from .")),
            module.__dict__,
        )
    finally:
        del sys.modules[module.__name__]
    return module.__dict__[module.__all__[0]]


def test_a_root_required_the_branches_declare_is_root_required_and_not_a_field(
    tmp_path,
) -> None:
    """Section 5's ``required`` row at ROOT beside a union, both arms.

    The row reads "required on the base's fields, and the names recorded in
    ``_ROOT_REQUIRED``, so a refusal can separate a field the root requires from one
    that SELECTS A BRANCH" -- which presupposes that a name selecting a branch is not a
    field of the base.  ``lower.objects.fields`` refused the document instead, on the ground
    that the name is a presence rule with no field, and
    ``core/product-format-declaration.json`` was 1 of this row's 3 primary refusals and
    8 of the 11 documents the row held.

    The ``jsonschema`` lines are what make this a measurement: the document refuses a
    payload carrying only ``label`` and admits one carrying both branch keys, so the
    claim about the model is a claim about the document's own accepted set and not
    about the rendering.  Both directions are asserted, because a base that gained a
    required ``kind`` FIELD would also refuse the first payload -- and would then state
    a ``properties`` entry its document does not.
    """
    judged = _union_root(["kind", "value"])
    control = _union_root(["label"])
    assert not jsonschema.Draft7Validator(judged).is_valid({"label": "x"})
    assert jsonschema.Draft7Validator(judged).is_valid({"kind": "a", "value": "s"})
    both = {"label": "x", "kind": "a", "value": "s"}
    assert jsonschema.Draft7Validator(control).is_valid(both)

    bundle_at = _write(tmp_path / "judged", {"core/probe.json": judged})
    out = emit.emit(bundle_at, ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    base = _emitted_model("core/probe.json", out)

    # The names are the BASE's record and not its fields: a field for either would
    # shadow the branches' own typed declaration with whatever the root says about it,
    # which is nothing.
    assert base._ROOT_REQUIRED == ("kind", "value"), base._ROOT_REQUIRED
    assert sorted(base.model_fields) == ["label"], sorted(base.model_fields)
    # **AND THE BASE'S RENDERED SCHEMA STATES NO ``required``.**  Pinned here rather
    # than left implicit: ``_ROOT_REQUIRED`` is a ``ClassVar`` and no
    # ``model_json_schema()`` carries one, so the document's two names appear nowhere in
    # the base's own rendering.  The fact is NOT dropped -- section 8 gives each branch
    # class "its branch node read UNDER THE ROOT'S SIBLINGS", where both names are the
    # branch's own ``required``, and the model refuses a payload omitting either
    # (below).  So what the base carries the names FOR is the refusal's attribution,
    # which is the clause above.
    assert "required" not in base.model_json_schema(), base.model_json_schema()

    # The accepted set, through the base's own dispatch: the branches' requiredness is
    # what refuses, and ``_ROOT_REQUIRED`` is what names it on the document's keyword.
    assert base.model_validate({"kind": "a", "value": "s"}).value == "s"
    try:
        base.model_validate({"label": "x"})
    except ValidationError as err:
        # The error TYPE and its LOCATION, which is the claim: ``_no_branch`` reports a
        # root-required field on the DOCUMENT's own ``required`` at its own location,
        # and the combinator only where nothing of ``_ROOT_REQUIRED`` is absent.
        reported = {(e["type"], e["loc"]) for e in err.errors()}
    else:
        raise AssertionError("a payload the document refuses was accepted")
    assert reported == {("required", ("kind",)), ("required", ("value",))}, reported

    # The control arm: a root ``required`` naming a root PROPERTY is a field's
    # requiredness exactly as it was, and ``_ROOT_REQUIRED`` carries it too.
    bundle_at = _write(tmp_path / "control", {"core/probe.json": control})
    out = emit.emit(bundle_at, ["core/probe.json"])
    assert out.refusals == {}, out.refusals
    other = _emitted_model("core/probe.json", out)
    assert other._ROOT_REQUIRED == ("label",), other._ROOT_REQUIRED
    assert other.model_json_schema()["required"] == ["label"], other.model_json_schema()
