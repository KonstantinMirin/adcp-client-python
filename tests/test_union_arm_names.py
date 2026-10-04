"""Union-arm names come from the schema node, never from a position (§3).

``scripts/union_arm_names.py`` answers one question — what is this arm called —
by the first rung that holds: title, discriminator const, full required set, fail
closed. These tests grade the answer against the bundle the pipeline actually
reads, ``schemas/cache/3.2`` (``resolve_bundle_key("3.2.1")`` -> ``3.2``),
excluding ``bundled/`` (self-contained by design) and ``mcp/`` (a per-profile
tree whose duplicates inflate any count taken over it).

The counts are pinned by EQUALITY, the way the version-envelope residue is: a
schema bump that moves one fails here and is read, rather than drifting under a
"greater than" that nobody revisits. They are measurements, not a ledger of
tolerated numbers — nothing is permitted by appearing in them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adcp._version import _read_packaged_version
from adcp.validation.version import resolve_bundle_key
from scripts.union_arm_names import (
    ArmName,
    UnnameableArmError,
    classify,
    classify_bundle,
    classify_document,
    derive,
    pascal_case,
    schema_files,
    tally,
    unnameable,
)


def _schema_dir() -> Path:
    return Path("schemas") / "cache" / resolve_bundle_key(_read_packaged_version())


@pytest.fixture(scope="module")
def bundle() -> list[ArmName]:
    return classify_bundle(_schema_dir())


def _names(relative: str) -> list[ArmName]:
    path = _schema_dir() / relative
    return classify_document(json.loads(path.read_text()), Path(relative))


def test_the_bundle_read_is_the_bundle_generation_reads() -> None:
    """A count over the wrong tree is the trap this records against."""
    assert _schema_dir() == Path("schemas/cache/3.2")
    assert len(schema_files(_schema_dir())) == 1057


def test_every_root_arm_is_classified_and_the_partition_is_exact(
    bundle: list[ArmName],
) -> None:
    """557 root arms, partitioned with nothing left over."""
    counts = tally(bundle)
    assert counts["root arms"] == 557
    assert counts["rung: title"] == 169
    assert counts["rung: const"] == 82
    assert counts["rung: required-set"] == 27
    assert counts["mints no class (ref)"] == 96
    assert counts["mints no class (scalar)"] == 10
    assert counts["mints no class (validation)"] == 172
    assert counts["rung 4: FAIL CLOSED"] == 1
    # The partition covers the population: named + class-less + refused == total.
    named = counts["rung: title"] + counts["rung: const"] + counts["rung: required-set"]
    classless = (
        counts["mints no class (ref)"]
        + counts["mints no class (scalar)"]
        + counts["mints no class (validation)"]
    )
    assert named + classless + counts["rung 4: FAIL CLOSED"] == counts["root arms"]


def test_exactly_one_arm_in_the_pinned_bundle_is_unnameable(bundle: list[ArmName]) -> None:
    """The single upstream title ARCH-ONE-SURFACE §7 costs the design.

    ``get-content-standards-response.json`` oneOf[0] is the success arm; it
    carries a ``description`` and no ``title`` while its sibling pattern
    (``create-media-buy-response.json``) titles all three arms. One metadata PR
    with in-tree precedent, and until it lands the rule refuses the name rather
    than minting a counter.
    """
    refused = unnameable(bundle)
    assert [item.pointer for item in refused] == [
        "content-standards/get-content-standards-response.json#/oneOf/0"
    ]


def test_the_titled_response_arms_get_the_names_the_schema_already_carries() -> None:
    """The example the whole rule exists for: 1/2/3 -> Success/Error/Submitted."""
    assert [
        (item.rung, item.name) for item in _names("media-buy/create-media-buy-response.json")
    ] == [
        ("title", "CreateMediaBuySuccess"),
        ("title", "CreateMediaBuyError"),
        ("title", "CreateMediaBuySubmitted"),
    ]


def test_the_const_rung_names_an_untitled_discriminated_arm() -> None:
    """``core/signal-ref.json``'s three scopes, named by their pinned value."""
    assert [(item.rung, item.name) for item in _names("core/signal-ref.json")] == [
        ("const", "SignalRefProduct"),
        ("const", "SignalRefDataProvider"),
        ("const", "SignalRefSignalSource"),
    ]


def test_the_required_set_rung_uses_the_full_set_not_the_difference() -> None:
    """``a2ui/bound-value.json`` is the case a set-difference gets wrong.

    Five arms require ``{literalString}``, ``{literalNumber}``,
    ``{literalBoolean}``, ``{path}`` and ``{literalString, path}``. Arm 4 is the
    conjunction of arms 0 and 3, so its difference against its siblings is EMPTY
    while the full sets are all distinct.
    """
    items = _names("a2ui/bound-value.json")
    assert all(item.rung == "required-set" for item in items)
    assert [item.name for item in items] == [
        "A2UIBoundValueLiteralString",
        "A2UIBoundValueLiteralNumber",
        "A2UIBoundValueLiteralBoolean",
        "A2UIBoundValuePath",
        "A2UIBoundValueLiteralStringPath",
    ]


def test_a_rung_falls_through_when_its_name_is_not_unique_among_siblings() -> None:
    """``core/audience-selector.json``: three arms pin the SAME const.

    Binary, categorical and numeric signal selectors all carry
    ``type: "signal"``, so the const rung names them identically. Each rung's
    candidate must be unique among the siblings or the rung does not hold —
    which is what keeps every rung position-free, not just rung 3. This case was
    found by the fail-closed collision refusal, not by reading the bundle.
    """
    items = _names("core/audience-selector.json")
    assert [item.rung for item in items] == [
        "required-set",
        "required-set",
        "required-set",
        "const",
    ]
    assert len({item.name for item in items}) == 4


def test_a_validation_arm_is_refused_before_any_rung_runs() -> None:
    """Step zero: an arm introducing no property names nothing.

    ``media-buy/create-media-buy-request.json`` anyOf arms refine
    ``budget_allocation``/``packages``/``proposal_id`` — all declared on the base
    — with ``required`` and ``not``. They are validation constraints, and a
    public class for one would name something no buyer sends. Two of the three
    even carry a ``title``, which is why the classifier runs BEFORE the rungs.
    """
    items = _names("media-buy/create-media-buy-request.json")
    assert len(items) == 3, "fixture assumes a three-arm root anyOf"
    assert {item.kind for item in items} == {"validation"}
    assert {item.name for item in items} == {None}
    # anyOf[2] declares ONLY ``required`` and ``not`` — no ``type``, no
    # ``properties`` — which is why a "nothing structural, therefore scalar"
    # fallback cannot be the classifier's shape.
    assert items[2].kind == "validation"


def test_the_classifier_separates_a_type_arm_from_a_refinement_of_one() -> None:
    """The predicate itself, on the two shapes, with no schema file involved."""
    base = {"account": {"type": "object"}}
    refinement = {"properties": {"account": {"required": ["brand", "operator"]}}}
    real_arm = {"type": "object", "properties": {"media_buy_id": {"type": "string"}}}
    assert classify(refinement, base) == "validation"
    assert classify(real_arm, base) == "type"
    assert classify({"$ref": "core/thing.json"}, base) == "ref"
    assert classify({"const": "asap"}, base) == "scalar"
    assert classify({"type": "string", "format": "date-time"}, base) == "scalar"


def test_the_rule_fails_closed_rather_than_numbering() -> None:
    """A type arm with nothing to derive from yields no name at all."""
    document = {"title": "Thing", "oneOf": [{"type": "object", "properties": {"a": {}}}]}
    name, rung = derive(document, document["oneOf"], 0, Path("core/thing.json"))
    assert name is None
    assert rung == "none"


def test_a_rung_whose_name_is_not_unique_does_not_hold() -> None:
    """Two siblings with the SAME title: the title rung is silent for both.

    Uniqueness is a property OF the rung, not a check after it, so a tie does
    not collide — it falls through. With nothing else to derive from, both arms
    reach rung 4 and the build refuses them by name rather than numbering them.
    """
    document = {
        "title": "Thing",
        "oneOf": [
            {"title": "Thing Alpha", "type": "object", "properties": {"a": {"type": "string"}}},
            {"title": "Thing Alpha", "type": "object", "properties": {"b": {"type": "string"}}},
        ],
    }
    items = classify_document(document, Path("core/thing.json"))
    assert [item.kind for item in items] == ["type", "type"]
    assert [item.name for item in items] == [None, None]


def test_two_arms_deriving_one_name_across_rungs_is_refused_with_both_pointers() -> None:
    """The collision refusal, fired on purpose.

    Rung uniqueness is per-rung, so one arm named by its title and another named
    by its const can still land on the same name. That is the case the refusal
    exists for: numbering them is the defect, and the build must stop and say
    which two schema nodes disagree.
    """
    document = {
        "title": "Thing",
        "oneOf": [
            {"title": "ThingAlpha", "type": "object", "properties": {"a": {"type": "string"}}},
            {
                "type": "object",
                "properties": {"kind": {"const": "alpha"}, "b": {"type": "string"}},
            },
        ],
    }
    with pytest.raises(UnnameableArmError) as excinfo:
        classify_document(document, Path("core/thing.json"))
    message = str(excinfo.value)
    assert "core/thing.json#/oneOf/0" in message
    assert "core/thing.json#/oneOf/1" in message
    assert "ThingAlpha" in message


def test_pascal_case_preserves_interior_capitals() -> None:
    """An arm title is often already PascalCase; ``capitalize`` would mangle it."""
    assert pascal_case("CreateMediaBuySuccess") == "CreateMediaBuySuccess"
    assert pascal_case("Explicit packages with fixed allocation") == (
        "ExplicitPackagesWithFixedAllocation"
    )
    assert pascal_case("data_provider") == "DataProvider"
    assert pascal_case("zip_plus_four") == "ZipPlusFour"


def test_no_derived_name_is_positional(bundle: list[ArmName]) -> None:
    """The property the whole rule exists to guarantee."""
    numbered = [item for item in bundle if item.name and item.name[-1].isdigit()]
    assert numbered == [], [item.pointer for item in numbered]
