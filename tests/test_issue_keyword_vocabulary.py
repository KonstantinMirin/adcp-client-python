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

from typing import Any

import pytest
from jsonschema import Draft7Validator
from pydantic import BaseModel, ValidationError

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
