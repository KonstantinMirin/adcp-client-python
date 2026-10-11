"""A request model may not require a field its schema root leaves to a branch.

WHY THIS IS NOT COVERED BY ``test_schema_model_parity``. That module synthesizes
ONE document per tool, grows it to include the optional properties, and then
mutates LEAF VALUES at json pointers. A branch-selecting property is never
OMITTED, so the corpus cannot reach "drop ``creatives``, supply ``assignments``"
— and it does not. The parity suite passed 86/86 both with and against the defect
below; that is measured, not assumed, which is why this file exists rather than a
case being added there.

THE DEFECT IT GRADES. ``creative/sync-creatives-request.json`` requires only
``[idempotency_key, account]`` at its root and then offers

    anyOf: [{required: [creatives]}, {required: [assignments]},
            {required: [assignment_operations]}]

so a schema-valid request may carry ``assignments`` or ``assignment_operations``
INSTEAD of ``creatives``. The public ``SyncCreativesRequest`` redeclared
``creatives`` as required, and the SDK therefore refused two of the three legal
request shapes. Measured against the pinned schema with ``jsonschema``, one
document per branch:

    assignments branch              schema ACCEPTS   model REFUSED
    assignment_operations branch    schema ACCEPTS   model REFUSED
    creatives branch                schema ACCEPTS   model accepted

An ``anyOf`` branch's ``required`` is a condition on THAT branch, never on the
root. Narrowing a redeclared field's item type is right; dropping ``| None`` from
it is what made the other branches unreachable (salesagent-8qela.69).

THE POPULATION IS DERIVED, and asserted non-empty before anything is compared,
because a derivation that matches nothing passes while grading nothing.

SCOPED TO REQUESTS ON PURPOSE, AND THE WIDENING IS BLOCKED RATHER THAN UNWANTED.
The same defect exists on ``core/product.json`` (``format_options`` required by
``Product`` and by no root), and that fix is measured but NOT graded here: its
branch carries a ``title``, so the "purely ``required``" rule excludes it.
Relaxing that rule to ignore annotation-only keywords (``title``,
``description``, ``deprecated``) would admit Product — and also
``core/creative-asset.json`` and ``core/creative-manifest.json``, whose public
models are STILL over-required for a different reason (a oneOf branch class above
the root in their MRO, salesagent-8qela.69). Widening now would need those two
allowlisted, so the widening waits until they are fixed and then costs one line
here and no allowlist. A request model refusing a legal request is the severe
case and is covered.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import adcp.types as public_types
from adcp.validation.version import resolve_bundle_key

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE_KEY = resolve_bundle_key((_REPO_ROOT / "src" / "adcp" / "ADCP_VERSION").read_text().strip())
_SCHEMA_DIR = _REPO_ROOT / "schemas" / "cache" / _BUNDLE_KEY

#: Measured at the 3.2.1 pin: 8 request schemas select a branch purely by
#: ``required``, carrying 25 branches between them. A floor, not an equality —
#: the bundle grows between AdCP releases — and the population assertion this
#: test needs, since an empty population would compare an empty list and pass.
_MIN_BRANCH_SELECTING_SCHEMAS = 6


def _branch_selecting_requests() -> list[tuple[Path, dict[str, Any], str, list[list[str]]]]:
    """Every request schema whose root offers a choice stated purely as ``required``.

    "Purely" matters: a branch carrying ``properties`` or ``not`` alongside its
    ``required`` is saying something about shape as well as presence, and reading
    its ``required`` as optional-at-the-root would not follow. A branch whose only
    keyword IS ``required`` says exactly "this property may be the one you send".
    """
    found = []
    for path in sorted(_SCHEMA_DIR.rglob("*-request.json")):
        relative = path.relative_to(_SCHEMA_DIR)
        if relative.parts[0] in ("mcp", "bundled"):
            continue
        schema = json.loads(path.read_text())
        if not isinstance(schema, dict):
            continue
        for keyword in ("anyOf", "oneOf"):
            pure = [
                branch
                for branch in schema.get(keyword) or []
                if isinstance(branch, dict) and set(branch) == {"required"}
            ]
            if len(pure) >= 2:
                found.append((relative, schema, keyword, [b["required"] for b in pure]))
    return found


def _public_model(stem: str) -> Any:
    """The public model for a schema stem, or ``None`` when the tool has no model."""
    return getattr(
        public_types, "".join(w.capitalize() for w in stem.replace("-", " ").split()), None
    )


_POPULATION = _branch_selecting_requests()


def test_the_branch_selecting_population_is_not_empty() -> None:
    """The derivation resolves, so the test below is comparing something."""
    assert len(_POPULATION) >= _MIN_BRANCH_SELECTING_SCHEMAS, (
        f"only {len(_POPULATION)} request schemas select a branch by `required`, expected at "
        f"least {_MIN_BRANCH_SELECTING_SCHEMAS} — the derivation has stopped resolving and the "
        "requiredness test below no longer grades anything"
    )
    stems = {relative.stem for relative, *_ in _POPULATION}
    assert "sync-creatives-request" in stems, (
        "sync-creatives-request is the known case this test was written for and it is "
        f"absent from the derived population: {sorted(stems)}"
    )


@pytest.mark.parametrize(
    ("relative", "schema", "keyword", "branches"),
    _POPULATION,
    ids=[str(relative) for relative, *_ in _POPULATION],
)
def test_no_request_model_requires_what_its_root_leaves_to_a_branch(
    relative: Path, schema: dict[str, Any], keyword: str, branches: list[list[str]]
) -> None:
    model = _public_model(relative.stem)
    if model is None:
        pytest.skip(f"{relative} has no public request model")

    root_required = set(schema.get("required") or [])
    over_required = sorted(
        name
        for name, field in model.model_fields.items()
        if field.is_required() and name not in root_required
    )
    selected = sorted({name for branch in branches for name in branch})
    assert over_required == [], (
        f"{model.__name__} requires {over_required}, which {relative} does not require at its "
        f"root (root requires {sorted(root_required)}). Its {keyword} offers {selected} as "
        f"alternatives, so a document choosing another one is schema-valid and this model "
        f"refuses it. A branch's `required` is a condition on that branch, not on the root."
    )
