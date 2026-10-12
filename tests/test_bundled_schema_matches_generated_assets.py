"""The bundled schema's asset-type discriminators must all exist as generated classes.

WHY THIS FILE EXISTS. One wheel shipped a bundled ``core/format.json`` declaring 21
``asset_type`` discriminators while its generated classes modelled 14, with 12 in
the ``repeatable_group`` arm against the schema's 21 — a codegen/schema divergence
INSIDE A SINGLE ARTIFACT. The suite was green throughout, because nothing in it
compared the two sides. It surfaced only when an adopter derived one side from the
generated classes and the other from the bundled schema.

So the defect was not that a check failed; it was that no check existed. Both
halves ship in the same wheel, both are derived from the same source at build
time, and a reader of either alone cannot see them disagree.

THE UNION IS NESTED, which is why a casual reader returns zero. ``core/format.json``
discriminates first on ``item_type`` (``individual`` / ``repeatable_group``) and
only then on ``asset_type``, and the two arms nest to DIFFERENT depths — the
``individual`` arm carries its inner ``oneOf`` at the arm's own level while
``repeatable_group``'s sits deeper. A fixed-depth walk therefore derives the full
set for one arm and nothing for the other, so both sides here walk the whole
subtree rather than a known shape.

BOTH POPULATIONS ARE ASSERTED NON-EMPTY, and that is not decoration: a guard whose
population feeds a comparison reports success when the population empties. An
empty schema side would compare cleanly against anything.
"""

from __future__ import annotations

import json
from typing import Any, get_args

import pytest

from adcp.types import FormatAssetUnion, RepeatableAssetGroup
from adcp.validation.schema_loader import _resolve_schema_root


def _asset_type_consts(node: Any, found: set[str] | None = None) -> set[str]:
    """Every ``asset_type`` ``const`` anywhere under ``node``.

    Whole-subtree rather than a fixed path: see the module docstring on the two
    arms nesting to different depths.
    """
    found = set() if found is None else found
    if isinstance(node, dict):
        declared = node.get("asset_type")
        if isinstance(declared, dict) and isinstance(declared.get("const"), str):
            found.add(declared["const"])
        for value in node.values():
            _asset_type_consts(value, found)
    elif isinstance(node, list):
        for value in node:
            _asset_type_consts(value, found)
    return found


def _generated_asset_types(annotation: Any, found: set[str] | None = None) -> set[str]:
    """Every ``asset_type`` field default reachable from ``annotation``.

    The discriminator lives in a pydantic FIELD DEFAULT, not in a ``Literal[...]``
    written into a generated file — a text search over the generated module finds
    an import of ``UrlAssetType`` and nothing else, which is how this divergence
    reads as absent when it is present.

    Descends through union members AND through model fields: a group arm reaches
    its asset classes through a field annotation, so walking union arguments alone
    returns the empty set for it.
    """
    found = set() if found is None else found
    fields = getattr(annotation, "model_fields", None)
    if fields is not None:
        default = getattr(fields.get("asset_type"), "default", None)
        if isinstance(default, str):
            found.add(default)
        for field in fields.values():
            _generated_asset_types(field.annotation, found)
    for argument in get_args(annotation):
        _generated_asset_types(argument, found)
    return found


@pytest.fixture(scope="module")
def bundled_format_schema() -> dict[str, Any]:
    """``core/format.json`` as the WHEEL ships it.

    Resolved through the SDK's own ``_resolve_schema_root``, which prefers the
    packaged ``adcp/_schemas`` copy and falls back to the repo layout, so this
    grades the artifact an adopter installs rather than a path spelled here.
    """
    root = _resolve_schema_root()
    assert root is not None, "no bundled schema tree resolved for the SDK's pinned version"
    path = root.core / "format.json"
    if not path.exists():
        path = root.bundled / "core" / "format.json"
    assert path.exists(), f"bundled core/format.json not found under {root.root}"
    return json.loads(path.read_text())


def test_the_schema_declares_asset_types(bundled_format_schema: dict[str, Any]) -> None:
    """The authority side is non-empty, so the comparison below grades something."""
    assert _asset_type_consts(bundled_format_schema), (
        "the bundled schema declared no asset_type const; the comparison would "
        "pass against any generated set, including an empty one"
    )


def test_the_generated_classes_declare_asset_types() -> None:
    """The subject side is non-empty too, for the same reason in reverse."""
    assert _generated_asset_types(FormatAssetUnion) or _generated_asset_types(
        RepeatableAssetGroup
    ), "no generated class carried an asset_type default; the walk found nothing to compare"


def test_every_bundled_asset_type_has_a_generated_class(
    bundled_format_schema: dict[str, Any],
) -> None:
    """The comparison the shipped wheel could not make about itself.

    One direction only: the schema is the authority, so a discriminator it
    declares MUST have a class. A generated class with no schema const would be a
    different defect and is not asserted here, because the generator legitimately
    models shapes the format schema does not discriminate on.
    """
    declared = _asset_type_consts(bundled_format_schema)
    generated = _generated_asset_types(FormatAssetUnion) | _generated_asset_types(
        RepeatableAssetGroup
    )
    missing = sorted(declared - generated)
    assert not missing, (
        f"{len(missing)} of {len(declared)} asset_type discriminators in the bundled "
        f"core/format.json have no generated class: {missing}. The schema and the "
        f"classes ship in one wheel and disagree."
    )
