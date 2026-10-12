"""``issues[].keyword`` is a JSON Schema keyword, on every refusal that ships one.

``core/error.json`` asks for a keyword "drawn from the JSON Schema vocabulary …
Implementers SHOULD use the validator's native keyword name; do not invent
custom values here", and the pinned prose makes it a MUST --
``building/by-layer/L3/error-handling.mdx``, Production-emit rules: "``keyword``
MUST be drawn from the JSON Schema Draft 7 / 2020-12 vocabulary". The field is
REQUIRED on every entry, so there is no conformant option of leaving it out.

The projection maps every pydantic type it recognises onto such a keyword and
falls back to ``validation`` for the two OPAQUE ones, ``value_error`` and
``assertion_error``. ``validation`` is not in the vocabulary, deliberately: the
raise site knows which schema construct it implements and the projection cannot,
so a blanket mapping would put a confident wrong keyword on the wire in place of
a recognisably wrong one. The fix for a failure here is therefore at the raise
site -- ``PydanticCustomError(<keyword>, …)`` -- never a widening of
:func:`adcp.validation.pydantic_errors._keyword`.

Scope, stated because a green here is not a green for the whole tree: this
grades the SPLIT ROOTS, whose refusals are reachable with a one-key document.
80 ``raise ValueError(...)`` sites exist under ``src/adcp/types`` across 26
modules, and any of them reaching ``issues[]`` is the same violation; this
population covers the one class measured reaching the wire
(salesagent-8qela.94).
"""

from __future__ import annotations

import ast
import pathlib
from typing import Any

import pytest
from jsonschema import Draft7Validator
from pydantic import BaseModel, ValidationError

import adcp.types
from adcp.validation.pydantic_errors import issues_from_validation_error

# The one derivation of "every class that declares its branches", with the
# reasoning for why declaring the method is the selector. A second walk here
# would be a second answer to the same question.
from tests.test_branch_dispatch_on_every_path import _roots_with_branches

#: Taken from the validator that implements the vocabulary rather than restated,
#: so the set cannot drift from the thing the pin points at.
VOCABULARY = frozenset(Draft7Validator.VALIDATORS)

SPLIT_ROOTS = sorted(_roots_with_branches().items())


def test_split_roots_were_discovered() -> None:
    """A population of nothing makes every assertion below vacuous."""
    assert len(SPLIT_ROOTS) >= 19, [name for name, _ in SPLIT_ROOTS]


def _documents(root: type[BaseModel]) -> list[dict[str, Any]]:
    """The empty document, and one carrying each declared field alone.

    A branch forbids the fields its siblings require, so a single-key document
    is the shortest thing that reaches a forbidden-name refusal -- which is the
    refusal that was emitting a non-vocabulary keyword. Derived from the root's
    own fields rather than authored per root.
    """
    return [{}] + [{name: "x"} for name in root.model_fields]


@pytest.mark.parametrize(("name", "root"), SPLIT_ROOTS, ids=[n for n, _ in SPLIT_ROOTS])
def test_every_keyword_a_split_root_emits_is_in_the_vocabulary(
    name: str, root: type[BaseModel]
) -> None:
    offenders: list[tuple[str, str]] = []
    for document in _documents(root):
        try:
            root.model_validate(document)
        except ValidationError as error:
            for issue in issues_from_validation_error(error):
                if issue.keyword not in VOCABULARY:
                    offenders.append((issue.keyword, next(iter(document), "{}")))
    assert not offenders, f"{name} emitted keywords outside the JSON Schema vocabulary: {offenders}"


def test_the_population_actually_produces_keywords() -> None:
    """Refusals reach the projection at all.

    Without this, a root that accepted every probe document would contribute no
    issue, and the test above would pass by never looking at a keyword. Asserted
    over the whole population rather than per root, since a root is allowed to
    accept a one-key document.
    """
    seen: set[str] = set()
    for _name, root in SPLIT_ROOTS:
        for document in _documents(root):
            try:
                root.model_validate(document)
            except ValidationError as error:
                seen.update(issue.keyword for issue in issues_from_validation_error(error))
    assert seen, "no split root refused any probe document, so no keyword was graded"
    assert seen <= VOCABULARY, sorted(seen - VOCABULARY)


# ---------------------------------------------------------------------------
# The remainder, bounded rather than fixed.
#
# A bare ``raise ValueError`` reaches pydantic as ``value_error``, which has no
# JSON Schema equivalent, so any such raise that reaches ``issues[]`` carries the
# out-of-vocabulary fallback. The one site measured reaching the wire is fixed
# (``_conditions.absent``); the rest each need a per-site judgment about WHICH
# keyword they compile, and a confident wrong keyword on the wire is worse than a
# recognisably wrong one. So the count is frozen and allowed to shrink while
# those judgments are made.
#
# PER MODULE, not a total. A ceiling of 80 is satisfiable by adding a site to
# ``core.py`` and removing one from ``canonical_creative.py``, which is the one
# outcome a ratchet exists to prevent.
#
# To shrink an entry: give the raise site its keyword --
# ``PydanticCustomError(<keyword>, ...)`` where the keyword names the schema
# construct the check compiles -- then lower the number here. The stale half of
# the assertion below fails if you forget, which is the desired behaviour.
# ---------------------------------------------------------------------------

#: Paths relative to ``src/adcp/types``. Measured at 1eae4b862: 80 sites in 26
#: modules, down from 81 in 27 before ``_conditions.absent`` was given its
#: keyword.
BARE_VALUE_ERROR_BASELINE: dict[str, int] = {
    "_geo_place_keys.py": 1,
    "aliases.py": 1,
    "canonical_creative.py": 11,
    "canonical_decl.py": 2,
    "core.py": 13,
    "domains/adagents.py": 3,
    "domains/bundled/protocol/get_adcp_capabilities_response.py": 3,
    "domains/core/creative_representation.py": 1,
    "domains/core/placement_presentation.py": 1,
    "domains/core/postal_area.py": 1,
    "domains/core/presentation_ref.py": 1,
    "domains/core/preview_provider.py": 1,
    "domains/core/reference_renderer.py": 2,
    "domains/core/reporting_delivery_capabilities.py": 3,
    "domains/core/reporting_delivery_config.py": 4,
    "domains/core/transformer.py": 1,
    "domains/media_buy/change_term.py": 1,
    "domains/media_buy/change_term_constraints.py": 4,
    "domains/media_buy/commercial_terms.py": 7,
    "domains/media_buy/get_media_buy_delivery_request.py": 2,
    "domains/media_buy/legacy_purchase_continuation_input.py": 3,
    "domains/trusted_match/identity_match_response.py": 1,
    "domains/trusted_match/provider_registration.py": 6,
    "projections.py": 2,
    "versioned.py": 4,
    "versioned_bases/_runtime.py": 1,
}

_TYPES_ROOT = pathlib.Path(adcp.types.__file__).parent


def _bare_value_error_counts() -> dict[str, int]:
    """``raise ValueError(...)`` per module under ``adcp.types``, by parsing.

    One derivation, module-scoped. Walking each FUNCTION and calling
    ``ast.walk`` on it instead double-counts every nested raise, because
    ``ast.walk`` on an outer function also reaches the bodies of functions
    defined inside it -- which is how this count was first reported as 83.
    """
    counts: dict[str, int] = {}
    for path in sorted(_TYPES_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - shipped modules parse
            continue
        found = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Raise)
            and isinstance(node.exc, ast.Call)
            and getattr(node.exc.func, "id", getattr(node.exc.func, "attr", "")) == "ValueError"
        )
        if found:
            counts[path.relative_to(_TYPES_ROOT).as_posix()] = found
    return counts


def test_no_module_grows_its_bare_value_error_count() -> None:
    """The remainder only shrinks, and it shrinks where it is recorded."""
    counts = _bare_value_error_counts()
    messages: list[str] = []

    for module, found in sorted(counts.items()):
        allowed = BARE_VALUE_ERROR_BASELINE.get(module)
        if allowed is None:
            messages.append(
                f"  NEW module with a bare ValueError: {module} ({found}). "
                "Raise PydanticCustomError(<keyword>, ...) naming the schema "
                "construct the check compiles."
            )
        elif found > allowed:
            messages.append(f"  {module}: {found} raises, baseline {allowed}")

    # The stale half. Without it a fixed site leaves its number behind, the
    # ceiling drifts upward of reality, and a later regression lands under it
    # unnoticed.
    for module, allowed in sorted(BARE_VALUE_ERROR_BASELINE.items()):
        found = counts.get(module, 0)
        if found < allowed:
            messages.append(
                f"  STALE: {module} now has {found} (baseline {allowed}) — "
                "lower it in BARE_VALUE_ERROR_BASELINE."
            )

    if messages:
        raise AssertionError(
            "src/adcp/types bare-ValueError ratchet (salesagent-8qela.94):\n" + "\n".join(messages)
        )


def test_the_baseline_is_a_distribution_not_a_total() -> None:
    """The pin is per module, which is what a bare total cannot do.

    A single ceiling is satisfied by moving a violation between modules. This
    asserts the shape the condition requires: more than one module, and the
    recorded total agreeing with the sum, so neither can be edited alone.
    """
    assert len(BARE_VALUE_ERROR_BASELINE) > 1
    assert sum(BARE_VALUE_ERROR_BASELINE.values()) == 80, (
        "the recorded distribution no longer sums to the measured baseline; "
        "shrink an entry rather than adjusting this number"
    )
