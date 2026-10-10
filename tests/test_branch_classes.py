"""What an arm becomes when it is a type rather than a rule.

``scripts/branch_classes.py`` reads one ``Arm`` record and says three things
about the class that arm becomes: which fields it must not declare, which it
must require, and what is left over for a compiled check. The first two are why
a branch class makes a combination unspellable instead of refusing it, so each
is graded here on its own, and the leftover is graded for what it KEEPS rather
than only for what it drops -- a planner that quietly swallowed an arm's nested
content would read as a stronger model and be a weaker one.

The emitter is not wired into the generation pipeline. Four places used a split
root's public name as a BASE, and a union cannot be subclassed. The shared base
settles two of them -- ``Creative(CreativeAsset)`` and
``CreativeRepresentation(CreativeManifest)`` are generated, and the emitter
repoints them onto the base, which is graded below. The remaining two are the
hand-written create-media-buy layers (``canonical_creative`` narrows
``packages``, and ``_forward_compat`` rebuilds the model and declares a
static view of a runtime-patched field); those narrow PER ARM, so each needs a
class per arm and its own union, and that is the integration step.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, get_args

import pytest
from pydantic import ValidationError

from scripts.branch_classes import (
    plan_branches,
    render_absence_hook,
    repoint_subclasses_of,
    split_into_branch_classes,
)
from scripts.schema_constraints import (
    DeclaredShape,
    PropSatisfies,
    Restated,
    ValueConst,
    read_root_constraints,
)


def _constraints(root: dict[str, Any], fields: dict[str, str]) -> Any:
    return read_root_constraints(
        root,
        DeclaredShape(fields=fields, nested={name: DeclaredShape() for name in fields}),
        arms_render_as_classes=False,
    )


_TWO_ARMS: dict[str, Any] = {
    "title": "Thing",
    "type": "object",
    "properties": {"a": {}, "b": {}, "c": {}},
    "anyOf": [
        {"required": ["a"], "not": {"required": ["b"]}},
        {"required": ["b"], "not": {"required": ["a"]}},
    ],
}


def test_an_arm_forbids_a_field_by_not_declaring_it() -> None:
    """``not: {required: [b]}`` is the absence of the field, not a check on it."""
    first, second = plan_branches(
        _constraints(_TWO_ARMS, {"a": "a", "b": "b", "c": "c"}),
        "Thing",
        "core/thing.json",
        frozenset({"a", "b", "c"}),
    )

    assert first.absent == frozenset({"b"})
    assert first.required == frozenset({"a"})
    assert second.absent == frozenset({"a"})
    assert second.required == frozenset({"b"})
    assert first.residual == Restated("arm") and second.residual == Restated(
        "arm"
    ), "requiredness and absence are the whole of these arms, so no check is left"


def test_a_banned_pair_stays_a_check_because_neither_name_is_forbidden() -> None:
    """``not: {required: [a, b]}`` forbids the COMBINATION, not either field.

    Dropping either field would refuse a document the schema accepts, so the
    planner leaves the conjunct to the compiled check. ``webhook-challenge-
    response`` states its ban this way.
    """
    root = {
        "title": "Thing",
        "type": "object",
        "properties": {"a": {}, "b": {}},
        "not": {"required": ["a", "b"]},
        "anyOf": [{"required": ["a"]}, {"required": ["b"]}],
    }

    first, _second = plan_branches(
        _constraints(root, {"a": "a", "b": "b"}), "Thing", "core/thing.json", frozenset({"a", "b"})
    )

    assert first.absent == frozenset()
    assert first.residual != Restated("arm"), "the ban must survive as a check"


def test_a_const_on_a_declared_field_becomes_a_literal_not_a_check() -> None:
    """A discriminator is the field's type on that arm.

    The sibling ``type`` is dropped only because the ``const`` it accompanies
    becomes the annotation; without that, dropping it would lose a constraint.
    """
    root = {
        "title": "Thing",
        "type": "object",
        "properties": {"status": {}, "a": {}},
        "oneOf": [
            {
                "required": ["status", "a"],
                "properties": {"status": {"type": "string", "const": "completed"}},
            },
            {"required": ["status"], "properties": {"status": {"const": "failed"}}},
        ],
    }

    first, second = plan_branches(
        _constraints(root, {"status": "status", "a": "a"}),
        "Thing",
        "core/thing.json",
        frozenset({"status", "a"}),
    )

    assert first.literals == {"status": "completed"}
    assert second.literals == {"status": "failed"}
    assert first.residual == Restated("arm")


def test_a_nested_const_stays_a_check_because_the_field_is_not_the_subject() -> None:
    """``budget_allocation.mode`` is one level down, so the arm's field set cannot carry it.

    Named as a check rather than silently dropped: this is the measured limit of
    what the branch class's own shape expresses, and what the arm's compiled
    validator is for.
    """
    root = {
        "title": "Thing",
        "type": "object",
        "properties": {"budget_allocation": {}, "packages": {}},
        "anyOf": [
            {
                "required": ["packages"],
                "properties": {"budget_allocation": {"properties": {"mode": {"const": "fixed"}}}},
            },
            {"required": ["budget_allocation"]},
        ],
    }

    first, _ = plan_branches(
        _constraints(root, {"budget_allocation": "budget_allocation", "packages": "packages"}),
        "Thing",
        "core/thing.json",
        frozenset({"budget_allocation", "packages"}),
    )

    assert first.literals == {}
    assert first.residual == PropSatisfies(
        "budget_allocation", PropSatisfies("mode", ValueConst("fixed"))
    )


def test_an_absence_set_is_also_refused_on_the_raw_document() -> None:
    """A field that is not declared is unspellable; a raw key still needs refusing.

    The generated models are ``extra='allow'`` where their schemas say
    ``additionalProperties: true``, so pydantic would file the forbidden key
    under extras and accept. The hook is what the design names as the one place
    the type system alone cannot carry an arm's content.
    """
    first, _ = plan_branches(
        _constraints(_TWO_ARMS, {"a": "a", "b": "b", "c": "c"}),
        "Thing",
        "core/thing.json",
        frozenset({"a", "b", "c"}),
    )

    hook = render_absence_hook(first)

    assert "_ABSENT: ClassVar[frozenset[str]] = frozenset({'b'})" in hook
    assert "mode='before'" in hook
    assert (
        "_c.absent(\n            data, sorted(cls._ABSENT), sorted(cls._ABSENT_NULLABLE)\n        )"
    ) in hook


_FLAT_MODULE = '''from __future__ import annotations

from pydantic import Field

from adcp.types.base import AdCPBaseModel


class Thing(AdCPBaseModel):
    """A flat root over both arms."""

    a: str | None = None
    b: str | None = None
    c: str | None = None
'''


def test_the_split_module_declares_each_arm_and_a_union_over_them() -> None:
    """The root's public name becomes the alias; a member is what one constructs."""
    rewritten = split_into_branch_classes(
        _FLAT_MODULE,
        "Thing",
        _constraints(_TWO_ARMS, {"a": "a", "b": "b", "c": "c"}),
        "core/thing.json",
        frozenset({"a", "b", "c"}),
    )

    assert rewritten is not None
    assert "class _ThingBase(AdCPBaseModel):" in rewritten
    assert "class ThingA(_ThingBase):" in rewritten
    assert "class ThingB(_ThingBase):" in rewritten
    assert "Thing: TypeAlias = ThingA | ThingB" in rewritten
    assert "ThingAdapter: TypeAdapter[Thing] = TypeAdapter(Thing)" in rewritten
    base = rewritten.split("class _ThingBase(AdCPBaseModel):")[1].split("class ThingA")[0]
    assert "a: str | None = None" in base
    assert "b: str | None = None" in base
    assert "c: str | None = None" in base, "a field no arm constrains is declared once"
    # The arm that requires ``a`` restates only what it changes: ``a`` loses its
    # default, ``b`` becomes unpassable, and ``c`` is left to the base.
    arm = rewritten.split("class ThingA(_ThingBase):")[1].split("class ThingB")[0]
    assert "a: str\n" in arm
    assert "b: None = None" in arm
    assert "c:" not in arm


def test_every_arm_is_a_subclass_of_one_base_so_the_union_is_one_type() -> None:
    """The arms differ in requiredness, so they are one type -- not several.

    Measured over the eleven roots the emitter splits: every one has properties
    shared by all of its arms, and eight of the eleven have arms that constrain
    no property at all. A union of unrelated classes would say the arms are
    different types, and nothing in the schemas says that. This is also what
    gives the union a usable base: a caller can hold the shared fields, and a
    class elsewhere can subclass what the arms share.
    """
    from scripts.post_generate_fixes import compose_branch_module

    rewritten = compose_branch_module(
        _FLAT_MODULE,
        "Thing",
        _constraints(_TWO_ARMS, {"a": "a", "b": "b", "c": "c"}),
        "core/thing.json",
        frozenset({"a", "b", "c"}),
    )

    assert rewritten is not None
    namespace: dict[str, Any] = {}
    exec(  # noqa: S102 - the emitter's output is the subject; importing it is the test
        rewritten.replace("from __future__ import annotations", ""), namespace
    )
    base = namespace["_ThingBase"]
    members = get_args(namespace["Thing"])

    assert len(members) == 2
    assert all(issubclass(member, base) for member in members)
    assert {"a", "b", "c"} <= set(base.model_fields), "the base carries what the arms share"
    assert namespace["ThingAdapter"].validate_python({"a": "x"}).a == "x"
    with pytest.raises(ValidationError):
        namespace["ThingAdapter"].validate_python({"a": "x", "b": "y"})


def test_the_base_is_module_internal_because_the_union_is_the_contract() -> None:
    """Stated as a test so the visibility decision is recorded where it binds.

    A consumer parses a document and gets one of the members, so what it
    annotates is the alias. The base exists to hold the fields the arms share
    and to be subclassed by a class that needs them; nothing needs ``isinstance``
    against it. So it is importable and not exported.
    """
    rewritten = split_into_branch_classes(
        _FLAT_MODULE,
        "Thing",
        _constraints(_TWO_ARMS, {"a": "a", "b": "b", "c": "c"}),
        "core/thing.json",
        frozenset({"a", "b", "c"}),
    )

    assert rewritten is not None
    assert "class _ThingBase(" in rewritten, "underscore-prefixed: not part of the public surface"
    assert '"_ThingBase"' not in rewritten, "and never named in an __all__ the next pass writes"


def test_a_class_that_subclassed_the_flat_root_is_repointed_onto_the_base() -> None:
    """A union cannot be subclassed, so a subclass has to name the base.

    Two generated classes do this on the pin -- ``Creative(CreativeAsset)`` and
    ``CreativeRepresentation(CreativeManifest)`` -- and the rewrite is what lets
    the split ship without either of them losing the fields it was reaching for.
    """
    module = (
        "from ..core.thing import Thing\n"
        "\n"
        "\n"
        "class Extended(Thing):\n"
        "    extra: str | None = None\n"
    )

    rewritten = repoint_subclasses_of(module, "Thing")

    assert rewritten is not None
    assert "class Extended(_ThingBase):" in rewritten
    assert "from ..core.thing import Thing, _ThingBase" in rewritten
    assert repoint_subclasses_of(module, "Other") is None, "a module naming it in no base list"

    # A base nothing imports is a module that fails at import, so the rewrite
    # refuses rather than emitting one. The shape it understands is a single-line
    # import, which is what both sites on the pin use.
    with pytest.raises(RuntimeError, match="to extend with _ThingBase"):
        repoint_subclasses_of(
            "from ..core.thing import (\n    Thing,\n)\n\n\nclass Extended(Thing):\n    pass\n",
            "Thing",
        )


def test_the_split_drops_a_combinator_check_the_arms_shape_already_answers() -> None:
    """A flat validator left by the constraint pass must not be copied per arm.

    Copied, it would re-ask the whole combinator on every arm and would carry a
    return annotation naming the union. Its decorator is what makes it run, and
    an earlier version of the copier dropped decorators while keeping bodies --
    a validator that reads as one and enforces nothing.
    """
    with_validator = _FLAT_MODULE + """
    @model_validator(mode='after')
    def _require_schema_required_group(self) -> Thing:
        if not (True):
            raise ValueError('nope')
        return self
"""

    rewritten = split_into_branch_classes(
        with_validator,
        "Thing",
        _constraints(_TWO_ARMS, {"a": "a", "b": "b", "c": "c"}),
        "core/thing.json",
        frozenset({"a", "b", "c"}),
    )

    assert rewritten is not None
    assert "raise ValueError('nope')" not in rewritten


def test_create_media_buys_three_arms_plan_as_the_design_measured_them() -> None:
    """The worked example, read off the pinned bundle rather than restated.

    Each arm's absence set is what makes the two red parity cases that combine
    arms unspellable: no class carries both ``packages`` and ``proposal_id``.
    """
    from scripts.post_generate_fixes import SCHEMA_DIR, flat_root_shape
    from scripts.schema_constraints import bundle_document_resolver

    relative = Path("media-buy/create-media-buy-request.json")
    schema = json.loads((SCHEMA_DIR / relative).read_text())
    shape = flat_root_shape(schema, relative)
    assert shape is not None
    constraints = read_root_constraints(
        schema,
        shape,
        arms_render_as_classes=False,
        schema_file=str(relative),
        resolve_document=bundle_document_resolver(SCHEMA_DIR),
    )

    plans = plan_branches(
        constraints, "CreateMediaBuyRequest", str(relative), frozenset(shape.fields.values())
    )

    by_name = {plan.name: plan for plan in plans}
    fixed = by_name["CreateMediaBuyRequestExplicitPackagesWithFixedAllocation"]
    proposal = by_name["CreateMediaBuyRequestCommittedProposalExecution"]

    assert fixed.absent == frozenset({"proposal_id"})
    assert "packages" in fixed.required
    assert proposal.absent == frozenset({"packages", "budget_allocation", "frequency_cap"})
    assert proposal.required >= frozenset({"proposal_id", "total_budget"})
    assert not (fixed.absent & fixed.required), "a field cannot be both forbidden and required"


def test_no_plan_forbids_a_field_it_also_requires() -> None:
    """Over the whole partitioning population, not just the worked example."""
    from scripts.post_generate_fixes import (
        SCHEMA_DIR,
        _root_generated_class,
        flat_root_shape,
        generated_module_for,
    )
    from scripts.schema_constraints import (
        bundle_document_resolver,
        partitions_by_requiredness,
        root_carries_constraints,
    )

    resolve = bundle_document_resolver(SCHEMA_DIR)
    graded = 0
    for schema_file in sorted(SCHEMA_DIR.rglob("*.json")):
        relative = schema_file.relative_to(SCHEMA_DIR)
        if relative.parts[0] in ("mcp", "bundled"):
            continue
        try:
            schema = json.loads(schema_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(schema, dict) or not root_carries_constraints(schema):
            continue
        shape = flat_root_shape(schema, relative)
        if shape is None:
            continue
        constraints = read_root_constraints(
            schema,
            shape,
            arms_render_as_classes=False,
            schema_file=str(relative),
            resolve_document=resolve,
        )
        if not constraints.combinator or not partitions_by_requiredness(constraints):
            continue
        parent = _root_generated_class(generated_module_for(relative).read_text(), schema)
        assert parent is not None
        for plan in plan_branches(
            constraints, parent, str(relative), frozenset(shape.fields.values())
        ):
            graded += 1
            assert not (plan.absent & plan.required), (relative, plan.name)
            assert plan.required, (relative, plan.name)

    assert graded > 15, f"only {graded} arms planned"


def test_a_module_without_the_flat_class_is_reported_not_guessed() -> None:
    assert (
        split_into_branch_classes(
            _FLAT_MODULE,
            "Missing",
            _constraints(_TWO_ARMS, {"a": "a", "b": "b", "c": "c"}),
            "core/thing.json",
            frozenset({"a"}),
        )
        is None
    )


def test_the_emitter_is_not_wired_into_the_generation_pipeline() -> None:
    """Stated as a test so the claim in the module docstring cannot go stale.

    Wiring it requires the two hand-written create-media-buy layers to narrow
    per arm, as the module docstring records; until then the roots it would
    split carry the compiled check that ``enforce_root_constraints`` emits, so
    nothing is parsed and left unenforced.
    """
    import inspect

    from scripts import post_generate_fixes

    source = inspect.getsource(post_generate_fixes.main)

    assert "emit_branch_classes" not in source
    assert "enforce_root_constraints" in source


def test_unused_import_guard() -> None:
    """Keeps ``pytest`` imported for the collection-time fixtures above."""
    assert pytest is not None
