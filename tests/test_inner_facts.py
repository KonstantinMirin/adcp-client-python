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

Every perturbation here is a PAIR of documents differing in the one key being judged,
so a passing arm and a failing arm are separated by the judged dimension and by
nothing else.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

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
    ``$ref`` row gives a ``description`` sibling and the same order ``compiler.fields``
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


def _defaults_on_required_properties() -> set[tuple[str, str]]:
    """Every (document, pointer) in the bundle where a property's declaration states a
    ``default`` -- its own, or its local ``$ref`` target's -- and its enclosing object
    REQUIRES the key.

    Read off the documents rather than off the run, so the set this check ranges over
    is a property of the bundle and the emitter's own record is what gets compared to
    it.  One level of ``properties`` only: the drop is reported at the pointer
    ``compiler.fields`` is handed, and a nested object's own properties are reached
    through their own node at their own pointer, which this enumerates too by walking
    every node the bundle yields.
    """
    found = set()
    for document in bundle.portable(BUNDLE):
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document)):
            props = node.get("properties") if isinstance(node, dict) else None
            demanded = node.get("required") if isinstance(node, dict) else None
            if not isinstance(props, dict) or not isinstance(demanded, list):
                continue
            for key, sub in props.items():
                if key in demanded and _stated_default(document, bundle.read(BUNDLE, document), sub) is not MISSING:
                    found.add((document, f"{pointer}/properties/{key}"))
    return found


def test_every_drop_the_run_reports_is_a_default_on_a_property_its_document_requires()\
        -> None:
    """The reported drops are exactly the shape section 5's row names, over the whole
    portable set, and the set is not empty.

    Both directions matter and only one of them is obvious.  A drop the bundle does
    not state at that shape would be the emitter discarding something else under this
    row's name; and the DOCUMENTS with the shape that this run never reached are
    reported as their own part rather than left in a difference of two totals, because
    a document refused on another row's keyword never reaches ``compiler.fields`` at
    all and its default is neither dropped nor rendered.
    """
    out = emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    reported = claimed(
        "drops the run reported",
        {(d, p) for d, sites in out.drops.items() for p in sites},
    )
    stated = claimed("defaults the bundle states on a required property",
                     _defaults_on_required_properties(), inside=None)
    assert reported <= stated, sorted(reported - stated)
    partitions(stated, reported=reported, never_reached=stated - reported)
    for document, pointer in sorted(reported):
        root = bundle.read(BUNDLE, document)
        node = root
        for step in [s for s in pointer.split("/") if s]:
            node = node[step] if not isinstance(node, list) else node[int(step)]
        assert out.drops[document][pointer] == _stated_default(document, root, node), (
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
STILL_REFUSED: dict[str, str] = {
    "core/assets/pixel-tracker-asset.json": "additionalProperties",
    "core/assets/url-asset.json": "additionalProperties",
    "core/media-buy.json": "$ref",
    "core/product-card-reference-asset.json": "$ref",
    "governance/get-plan-audit-logs-response.json": "$ref",
}


def test_every_document_this_row_releases_emits_and_the_rest_name_their_next_keyword()\
        -> None:
    """The named sets, over a fresh whole-population run.

    A total would be satisfied by any twelve documents.  This asserts the twelve the
    row owns and the seven it cleared a refusal for without finishing, which is what a
    later re-derivation of the ownership can be checked against.
    """
    out = emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    released = claimed(
        "documents this row releases",
        {d for names in RELEASED.values() for d in names},
        inside=bundle.portable(BUNDLE),
    )
    assert released <= set(out.emitted), sorted(released - set(out.emitted))
    cleared = claimed("documents whose next refusal is another row's", set(STILL_REFUSED))
    assert cleared.isdisjoint(released), sorted(cleared & released)
    for document, keyword in sorted(STILL_REFUSED.items()):
        row = out.refusals.get(document)
        assert row is not None, f"{document} now emits: move it out of STILL_REFUSED"
        assert row["keyword"] == keyword, (document, row)


# --------------------------------------------------------------------------- #
# the facts reach the model, which is what a named carrier is for
# --------------------------------------------------------------------------- #
def test_a_format_inside_a_container_reaches_the_models_own_schema() -> None:
    """The element's ``format`` is in the rendered schema, where the comparison reads
    it -- which is the whole point of naming the type rather than dropping it.

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
    except Exception:  # noqa: BLE001 -- the type is pydantic's and the claim is refusal
        pass
    else:
        raise AssertionError("the empty list was accepted: the branch lost its minItems")
    rendered = R.model_json_schema()["properties"]["status_filter"]
    array = next(b for b in rendered["anyOf"] if b.get("type") == "array")
    assert array["minItems"] == 1, rendered
    assert "minItems" not in rendered, "the bound reached the field holding the union"


def test_a_stores_extra_key_type_is_enforced_although_pydantic_renders_none() -> None:
    """The premise the comparison's ``extra_key_typed`` row rests on, measured.

    ``harness._extra_key_typed`` admits a ``propertyNames`` the model does not RENDER,
    on the ground that the model enforces it through the key type of its
    ``__pydantic_extra__``.  That is an admission, so its premise is graded here rather
    than left to the sentence that states it: a key one character past the document's
    ``maxLength: 128`` is refused and a short one is accepted, and the rendered schema
    really does carry no ``propertyNames``.
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
    except Exception:  # noqa: BLE001 -- the type is pydantic's and the claim is refusal
        return
    raise AssertionError("a key past the document's bound was accepted")
