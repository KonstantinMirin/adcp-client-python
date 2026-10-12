"""Every asset type the bundled schema declares must be ROUTABLE by the models.

WHY THE OBVIOUS COMPARISON IS THE WRONG ONE. The first version of this file
compared the bundled schema's ``asset_type`` consts against the generated
classes' ``asset_type`` defaults. That comparison passes on this tree, and it
would have passed at EVERY upstream release point including the broken ones,
because the generated classes always covered the vocabulary. The generated
artifact — ``adcp/types/domains/core/format.py`` — reads 42 ``asset_type:
Literal`` declarations (21 distinct, two arms) at v9.0.0-beta.1 through the
beta.4 release commit. Codegen was never the defect.

THE DEFECT IS A THIRD SIDE: WHAT THE MODELS ACTUALLY ROUTE. ``types/aliases.py``
carries two HAND-WRITTEN unions, and ``types/_forward_compat.py`` patches them
over the correct generated annotations at import. Upstream those unions carry 14
real arms individually and 12 in-group against the schema's 21, so seven
declared asset types (``card``, ``daast_tracker``, ``display_tag``,
``pixel_tracker``, ``published_post``, ``vast_tracker``, ``zip``) and nine
in-group fall through to the unknown arm. A schema-valid document deserializes as
``UnknownFormatAsset``.

SO THE ASSERTION IS: schema vocabulary == what ``Format.assets`` routes AFTER
forward-compat has been applied. Not what the generated classes declare, which is
correct and always was.

THE PATCH IS APPLIED BY A MODULE BODY, AND WHO TRIGGERS IT IS NOT FULLY PINNED.
``adcp.types._forward_compat`` calls ``_apply_forward_compat()`` when imported, so
this module imports it explicitly to guarantee the patched state is the one
graded. What is NOT established is that the explicit import is the only route:
measured on the 9.0.0b2 wheel, the walk reads 14 routable with or without it, so
something in the import chain already applies it there. The explicit import is
therefore a guarantee rather than the mechanism, and a reader should not take it
as evidence about which import arms the patch.

FIRE-PROBED IN BOTH DIRECTIONS ON REAL ARTIFACTS, not on a mutation. On this
fork it passes — schema 21, individual 21, group 21 — because ``0b8b194ab``
generates both unions and derives the vocabulary they route by. Run against the
``9.0.0b2+prs1435.1415.1447.1456`` wheel it FAILS, reading 14 individually and 12
in-group and naming exactly ``card``, ``daast_tracker``, ``display_tag``,
``pixel_tracker``, ``published_post``, ``vast_tracker``, ``zip`` (plus ``brief``
and ``catalog`` in-group).

That pair is what the first version of this file could not produce. Its probe
renamed a const in the bundled schema and watched the comparison go red, which
proves the comparison WORKS and says nothing about whether it is pointed at the
defect — the first version passed on the broken wheel too.

``routed_by`` is taken from the measurement in acp-branch-runs/repro, which is
where the walk was worked out. Its schema reader is not: that one resolves
``adcp.__file__ / "_schemas"``, which exists only in an installed wheel, so it
cannot run from an editable checkout. The reader here goes through the SDK's own
``_resolve_schema_root``, which prefers the packaged copy and falls back to the
repo layout — the same bytes in either case.

Refs: salesagent-8qela.168, salesagent-raqvy
"""

from __future__ import annotations

import json
import typing
from typing import Any

import pytest

# THE IMPORT THAT ARMS THE PATCH. Not a convenience and not reorderable: without
# it the generated annotations measure a correct 21/21 and this file grades
# nothing. Imported for its module-body side effect, hence the noqa.
import adcp.types._forward_compat  # noqa: F401
from adcp.types.aliases import RepeatableAssetGroup
from adcp.types.domains.core.format import Format
from adcp.validation.schema_loader import _resolve_schema_root


def _declared_by_schema(
    doc: Any, found: set[str] | None = None, key: str | None = None
) -> set[str]:
    """Every ``asset_type`` ``const`` anywhere under ``doc``.

    Whole-subtree rather than a fixed path: ``core/format.json`` discriminates on
    ``item_type`` first and ``asset_type`` second, and the two arms nest to
    DIFFERENT depths, so a fixed-depth walk derives the full set for one arm and
    the empty set for the other.
    """
    found = set() if found is None else found
    if isinstance(doc, dict):
        if key == "asset_type" and isinstance(doc.get("const"), str):
            found.add(doc["const"])
        for inner_key, value in doc.items():
            _declared_by_schema(value, found, inner_key)
    elif isinstance(doc, list):
        for value in doc:
            _declared_by_schema(value, found, key)
    return found


def _routed_by(model: type, field: str = "assets") -> set[str]:
    """Every ``asset_type`` a value of ``model.<field>`` can deserialize into.

    Walks the annotation rather than the class list, because the annotation is
    what forward-compat replaces and therefore what pydantic dispatches on.
    ``Annotated`` is unwrapped to its first argument so a discriminated union
    carrying field metadata is followed rather than treated as a leaf.
    """
    out: set[str] = set()
    stack = [model.model_fields[field].annotation]
    while stack:
        node = stack.pop()
        args = typing.get_args(node)
        if typing.get_origin(node) is typing.Annotated:
            stack.append(args[0])
            continue
        if args:
            stack.extend(args)
            continue
        declared = getattr(node, "model_fields", {}).get("asset_type")
        if declared is not None and isinstance(declared.default, str):
            out.add(declared.default)
    return out


@pytest.fixture(scope="module")
def declared() -> set[str]:
    """The schema's vocabulary, from the bundle the wheel ships."""
    root = _resolve_schema_root()
    assert root is not None, "no bundled schema tree resolved for the SDK's pinned version"
    path = root.core / "format.json"
    if not path.exists():
        path = root.bundled / "core" / "format.json"
    assert path.exists(), f"bundled core/format.json not found under {root.root}"
    return _declared_by_schema(json.loads(path.read_text()))


def test_the_schema_declares_asset_types(declared: set[str]) -> None:
    """The authority side is non-empty, so the comparisons below grade something.

    An empty authority compares cleanly against any subject, including an empty
    one, so this is the assertion that makes the others mean anything.
    """
    assert declared, "the bundled schema declared no asset_type const"


@pytest.mark.parametrize(
    ("label", "model"),
    [("Format.assets", Format), ("RepeatableAssetGroup.assets", RepeatableAssetGroup)],
    ids=["individual", "repeatable_group"],
)
def test_the_models_route_asset_types(label: str, model: type) -> None:
    """Each subject side is non-empty too, for the same reason in reverse."""
    assert _routed_by(model), f"{label} routes no asset_type; the walk found nothing to compare"


@pytest.mark.parametrize(
    ("label", "model"),
    [("Format.assets", Format), ("RepeatableAssetGroup.assets", RepeatableAssetGroup)],
    ids=["individual", "repeatable_group"],
)
def test_every_declared_asset_type_is_routable(declared: set[str], label: str, model: type) -> None:
    """The assertion the shipped wheel could not make about itself.

    One direction: the schema is the authority, so a type it declares MUST be
    routable. A routable type with no const would be a different question and is
    not asserted here.
    """
    unroutable = sorted(declared - _routed_by(model))
    assert not unroutable, (
        f"{len(unroutable)} of {len(declared)} asset types the bundled "
        f"core/format.json declares cannot be routed by {label}, so a schema-valid "
        f"document deserializes them as UnknownFormatAsset: {unroutable}"
    )
