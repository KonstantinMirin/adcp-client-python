"""A model must not accept a document and then emit one it would itself refuse.

A compiled root conjunct asks SENT-ness -- ``model_fields_set`` -- which is the
right question for ``required`` on an input and the wrong one for a conditional
the schema applies to the SERIALIZED document. There a default is
indistinguishable from a value the caller sent, so a defaulted field slips
through ``_c.descend`` (vacuous for a field that was not supplied) and is then
serialized. ``protocol/get-principal-response.json`` ties ``status`` to
``result.kind``; with ``status`` unset the model accepted a failed result and
dumped ``status='completed'``, which that conditional forbids (salesagent-38fdf).

THIS GRADES THE DEFECT, NOT A SHAPE. Two static descriptions of "the dangerous
shape" were tried first and neither selects the right set: "reads its own
defaulted field in the CHECK" admits 37 sites at this commit, most of them safe
because the check also demands the field be sent; adding "or in a guard with no
predicate" and excluding a check that demands sent-ness gives 9, which is a
DIFFERENT 9 from the 8 the bead's own probe found -- overlapping in the two real
escapes and disagreeing in both directions elsewhere. A count that matches is not
a set that matches.

So no shape is used. For each class that carries a conjunct and reads one of its
own fields that has a serializing default, a document the class ACCEPTS with that
field unset is synthesized, dumped, and fed back. If the class refuses its own
dump, it admitted a state its schema forbids and then emitted it. That is the
defect stated as itself, and it needs no allowlist: the expected answer is none.
"""

from __future__ import annotations

import ast
import inspect
import sys
import textwrap
from contextlib import contextmanager
from typing import Any, get_args

from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined

# Importing the consolidated module loads every generated domain module, and the
# canonical layer is a separate import. The derivation walks what is loaded.
import adcp.types._generated  # noqa: F401
import adcp.types.canonical_creative  # noqa: F401
from tests.conformance import _schema_parity as parity

#: The validator ``enforce_root_constraints`` emits, which is what makes a class
#: carry a compiled root conjunct at all.
ROOT_CONJUNCT = "_require_schema_required_group"


class _LocalDefs:
    """A ``$ref`` resolver over one pydantic schema's own ``$defs``."""

    def __init__(self, schema: dict[str, Any]) -> None:
        self._defs = schema.get("$defs", {})

    @contextmanager
    def resolving(self, ref: str) -> Any:
        yield self._defs[ref.rsplit("/", 1)[-1]]


def _generated_models() -> dict[tuple[str, str], type[BaseModel]]:
    """Every loaded model, keyed by ``(module, qualname)``.

    Both halves: an exported name hides aliases, and ``__qualname__`` alone
    collapses two distinct classes that share a name.
    """
    found: dict[tuple[str, str], type[BaseModel]] = {}
    for module in list(sys.modules.values()):
        if module is None or not getattr(module, "__name__", "").startswith("adcp.types"):
            continue
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, BaseModel):
                found[(value.__module__, value.__qualname__)] = value
    return found


def _conjunct_fields(model: type[BaseModel]) -> set[str]:
    """Every field name the class's own compiled conjunct reads off ``self``.

    Read from the validator's source rather than from the schema, because what
    the conjunct actually asks is what decides the escape -- and ``_c.descend``
    is the primitive that is vacuous for an unsupplied field.
    """
    function = model.__dict__.get(ROOT_CONJUNCT)
    if function is None:
        return set()
    raw = getattr(function, "__func__", function)
    raw = getattr(raw, "wrapped", raw)
    try:
        source = textwrap.dedent(inspect.getsource(raw))
    except (OSError, TypeError):
        return set()
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "_c"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "self"
            and isinstance(node.args[1], ast.Constant)
        ):
            names.add(node.args[1].value)
    return names


def _serializing_defaults(model: type[BaseModel], fields: set[str]) -> list[str]:
    """Those fields whose default is a value, so it reaches the wire."""
    out = []
    for name in sorted(fields):
        info = model.model_fields.get(name)
        if info is None:
            continue  # a nested member's field that happens to share a name
        if info.default is None or info.default is PydanticUndefined:
            continue  # nothing is emitted for it, so nothing can escape
        out.append(name)
    return out


def _accepted_documents_without(model: type[BaseModel], unset: list[str]) -> list[dict[str, Any]]:
    """Documents the model accepts which carry none of ``unset``."""
    schema = model.model_json_schema(mode="validation")
    try:
        candidates = parity.instances(schema, _LocalDefs(schema), budget=8)
    except Exception:
        return []
    good = []
    for candidate in candidates[:40]:
        if not isinstance(candidate, dict) or any(name in candidate for name in unset):
            continue
        try:
            model.model_validate(candidate)
        except ValidationError:
            continue
        good.append(candidate)
    return good


def _exposure() -> tuple[list[tuple[str, str, list[str]]], list[str]]:
    """``(graded, ungraded)`` over every class a conjunct could let a default escape."""
    graded: list[tuple[str, str, list[str]]] = []
    ungraded: list[str] = []
    for (module, qualname), model in sorted(_generated_models().items()):
        risky = _serializing_defaults(model, _conjunct_fields(model))
        if not risky:
            continue
        documents = _accepted_documents_without(model, risky)
        if not documents:
            ungraded.append(f"{module}.{qualname}")
            continue
        graded.append((module, qualname, risky))
    return graded, ungraded


def test_no_conjunct_lets_a_defaulted_value_escape_and_then_serializes_it() -> None:
    """The escape, stated as itself: accepted, then emitted and refused.

    Re-validating the DUMP is the whole assertion. If a class accepts a document
    and its own dump of that object does not validate, the conjunct graded a
    state the wire never carries -- which is what sent-ness asks and what the
    schema's conditional does not.
    """
    graded, _ungraded = _exposure()
    # A derivation that matches nothing is green, so the population is asserted.
    # Measured: 10 classes, 20 (class, field) pairs.
    assert len(graded) >= 10, f"the derivation selected only {len(graded)} classes to grade"

    escapes: list[str] = []
    for module, qualname, risky in graded:
        model = _generated_models()[(module, qualname)]
        for document in _accepted_documents_without(model, risky):
            dumped = model.model_validate(document).model_dump(mode="json", exclude_none=True)
            emitted = [name for name in risky if name in dumped]
            if not emitted:
                continue
            try:
                model.model_validate(dumped)
            except ValidationError as refusal:
                escapes.append(
                    f"{module}.{qualname}: accepted a document with {emitted} unset, then "
                    f"emitted {{{', '.join(f'{n}={dumped[n]!r}' for n in emitted)}}} and "
                    f"refused its own dump ({refusal.errors()[0]['type']})"
                )
                break

    assert not escapes, "\n".join(escapes)


def test_the_two_repaired_responses_grade_the_status_they_emit() -> None:
    """The two escapes 38fdf fixed, named, so the repair cannot be quietly undone.

    ``DERIVED_DEFAULTS`` in ``scripts/post_generate_fixes.py`` supplies ``status``
    from ``result.kind``, which makes it SENT so the conjunct grades it. Named
    here as well as covered by the derivation above, because the derivation
    depends on a document being synthesizable for these two classes and a
    schema refresh could take that away -- and then the one case anyone has
    actually seen escape would stop being graded with nothing failing.
    """
    from adcp.types.domains.protocol.get_principal_response import GetPrincipalResponse
    from adcp.types.domains.protocol.sync_principal_response import SyncPrincipalResponse

    failed = {
        "adcp_version": "3.2",
        "result": {"kind": "failed", "errors": [{"code": "AUTH_MISSING", "message": "no"}]},
    }
    for model in (GetPrincipalResponse, SyncPrincipalResponse):
        name = model.__name__
        # Unset: the status that reaches the wire is the one the conjunct permits.
        derived = model.model_validate(failed)
        assert derived.status.value == "failed", (
            f"{name} left status at {derived.status.value!r} for a failed result; the "
            "root conditional permits only 'failed' or 'rejected'"
        )
        dumped = derived.model_dump(mode="json", exclude_none=True)
        assert dumped["status"] == "failed"
        model.model_validate(dumped)  # the dump is a document it accepts

        # Explicitly contradicting the result is still refused, which is the
        # behaviour that was already correct and must not have been widened.
        with pytest_raises_validation(model, {**failed, "status": "completed"}):
            pass

        # A result that does not fire the conditional keeps the ergonomic default.
        # The non-failing arm is DERIVED per class: the two responses do not share
        # one -- get_principal has 'unconfigured', sync_principal does not -- and a
        # hardcoded arm made this test fail for the wrong reason.
        other = _a_non_failing_result(model)
        kept = model.model_validate({"adcp_version": "3.2", "result": other})
        assert kept.status.value == "completed", (
            f"{name} derived a status for result={other!r}, which does not fire the "
            "conditional, so the ergonomic default should stand"
        )


@contextmanager
def pytest_raises_validation(model: type[BaseModel], document: dict[str, Any]) -> Any:
    """``model`` refuses ``document``, named so the assertion reads in one line."""
    try:
        model.model_validate(document)
    except ValidationError:
        yield
        return
    raise AssertionError(f"{model.__name__} accepted {document!r}, which its conjunct forbids")


def _a_non_failing_result(model: type[BaseModel]) -> dict[str, Any]:
    """A ``result`` the class accepts whose ``kind`` is not the one that fires.

    Derived from the arms rather than written down, because the two repaired
    responses have different result vocabularies and only ``failed`` is common
    to both.
    """
    from adcp.types._split_root import branch_members

    annotation = model.model_fields["result"].annotation
    arms = branch_members(annotation) or get_args(annotation)
    for arm in arms:
        fields = getattr(arm, "model_fields", {})
        kind = fields.get("kind")
        if kind is None or kind.default == "failed":
            continue
        document: dict[str, Any] = {"kind": kind.default}
        schema = arm.model_json_schema(mode="validation")
        try:
            candidates = parity.instances(schema, _LocalDefs(schema), budget=8)
        except Exception:
            candidates = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            merged = {**candidate, **document}
            try:
                model.model_validate({"adcp_version": "3.2", "result": merged})
            except ValidationError:
                continue
            return merged
    raise AssertionError(f"{model.__name__} has no non-failing result arm to build")
