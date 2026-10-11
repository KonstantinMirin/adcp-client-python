"""A root with branches resolves to a branch on all three validation paths.

A ``model_validate`` override reaches ONE of them. Pydantic validates a nested
field and a ``TypeAdapter`` through the core schema, so an override is invisible
on both -- and both are production paths here: most roots with branches are
nested object schemas, and ``adcp.types.validation.validate_union`` (which the
server framework calls on a handler's return value) is a ``TypeAdapter``.

The response side shipped an override whose docstring said "runtime validators
continue to enforce the cross-field rules". It did not. Measured on the base it
guarded, with the override in place:

    validate_union(CreateContentStandardsResponse, {"totally": "wrong"})
    -> CreateContentStandardsResponse(model_extra={'totally': 'wrong'})

The base is ``extra="allow"``, so every field of an unrecognised document was
filed as an untyped extra and the document was accepted. This grades the
property that makes that docstring true, over every root with branches, on each
path -- so a mechanism that covers one path and not the others fails here rather
than passing three times on the one path it covers.
"""

from __future__ import annotations

import sys

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

# Importing the consolidated module is what loads every generated domain module,
# and the canonical layer is a separate import. The derivation below walks what
# is loaded, so a population derived before these imports is empty -- which is
# how the first version of this file parametrised over nothing and passed.
import adcp.types._generated  # noqa: F401
import adcp.types.canonical_creative  # noqa: F401


def _roots_with_branches() -> dict[str, type[BaseModel]]:
    """Every shipped class that DECLARES its branches.

    Declaring ``_branch_models`` is what makes a class the base -- the hook asks
    ``"_branch_models" in cls.__dict__``, not a registry -- so the same question
    the hook asks is the question that selects the population. All three sources
    are in it: a split root the branch emitter compiled, a response base whose
    numbered branches the generator wrote, and the canonical create request,
    which re-declares the method to dispatch to canonical branches.

    Keyed by module and class, not by exported name. Deriving over
    ``adcp.types.__all__`` found 11 of these, because ``CreativeAsset`` and
    ``CreativeManifest`` resolve to canonical REFINEMENTS of a single branch --
    which inherit the method, correctly keep their own shape, and are not bases
    over branches at all.
    """
    walked: dict[str, type[BaseModel]] = {}
    for module in list(sys.modules.values()):
        if module is None or not getattr(module, "__name__", "").startswith("adcp.types"):
            continue
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, BaseModel)
                and "_branch_models" in value.__dict__
            ):
                walked[f"{value.__module__}.{value.__name__}"] = value
    return walked


def _no_branch_accepts_the_empty_document(root: type[BaseModel]) -> bool:
    """Whether ``{}`` satisfies no branch of this root.

    The precondition of the probes below, asserted rather than assumed: a root
    with a branch that requires nothing accepts ``{}``, and expecting a refusal
    of it would be expecting the wrong thing. Three derived probes in this
    series passed vacuously because a precondition like this one went unchecked.
    """
    branches = root._branch_models()  # type: ignore[attr-defined]
    return bool(branches) and all(
        any(field.is_required() for field in branch.model_fields.values()) for branch in branches
    )


def _graded_roots() -> dict[str, type[BaseModel]]:
    return {
        name: root
        for name, root in _roots_with_branches().items()
        if _no_branch_accepts_the_empty_document(root)
    }


def _keywords(error: ValidationError) -> set[str]:
    return {entry["type"] for entry in error.errors()}


def test_a_document_satisfying_no_branch_is_refused_on_all_three_paths() -> None:
    """By name, nested in another model, and through a ``TypeAdapter``.

    Direct construction is graded alongside them, because it is the same core
    schema and because the loose base it used to produce is what let a root
    accept by construction the same empty document it refused by validation.

    The refusal names the root's own combinator on every path: ``core/error.json``
    requires each ``issues[]`` entry to carry a keyword from the JSON Schema
    vocabulary, and the ``missing`` pydantic reports is not in it.
    """
    graded = _graded_roots()
    assert graded, "the derivation selected no root to grade"

    for name, root in sorted(graded.items()):
        combinator = root._branch_combinator()  # type: ignore[attr-defined]
        assert combinator in {"anyOf", "oneOf"}, (name, combinator)

        class Holder(BaseModel):
            value: root  # type: ignore[valid-type]

        paths = {
            "by name": lambda root=root: root.model_validate({}),
            "nested": lambda holder=Holder: holder.model_validate({"value": {}}),
            "TypeAdapter": lambda root=root: TypeAdapter(root).validate_python({}),
            "constructed": root,
        }
        for path, call in paths.items():
            with pytest.raises(ValidationError) as caught:
                call()
            assert combinator in _keywords(caught.value), (
                f"{name} on the {path} path refused with "
                f"{sorted(_keywords(caught.value))}, not {combinator!r}"
            )


def test_the_population_covers_every_source_of_branches() -> None:
    """A derivation that matches nothing is green, so the floor is asserted.

    Thirteen split roots the branch emitter compiles, the five public response
    names whose numbered branches the generator writes, and the canonical create
    request. The floor is their sum; it is a floor because a schema refresh can
    only add roots that partition.
    """
    roots = _roots_with_branches()
    assert len(roots) >= 19, f"the derivation found only {len(roots)} roots with branches"

    graded = _graded_roots()
    # Measured: all 19. A root that stopped refusing it would mean some branch
    # requires nothing, which is a branch that accepts any document at all.
    assert len(graded) == len(
        roots
    ), f"{sorted(set(roots) - set(graded))} have a branch that requires nothing"

    # The five public response names are what this change adds to the
    # population. Named, not counted: a count of graded names ending in
    # "Response" is already satisfied by the split roots that happen to be
    # responses, so it would stay green with all five of these missing. The
    # generator's own list of them is hand-written, so this is auditable against
    # it rather than derived from the same place.
    for module, name in (
        ("compliance.comply_test_controller_response", "ComplyTestControllerResponse"),
        ("content_standards.create_content_standards_response", "CreateContentStandardsResponse"),
        ("content_standards.list_content_standards_response", "ListContentStandardsResponse"),
        ("content_standards.update_content_standards_response", "UpdateContentStandardsResponse"),
        ("account.sync_governance_response", "SyncGovernanceResponse"),
    ):
        key = f"adcp.types.domains.{module}.{name}"
        assert key in graded, f"{name} is not dispatching through its branches"

    # The canonical create request runs on the same mechanism. It used to carry
    # a second copy of the hook, keyed on class identity through two module
    # globals, and its own ``_branch_models`` -- inherited, not declared --
    # reported the GENERATED branches while that schema was built from the
    # canonical ones.
    canonical = "adcp.types.canonical_creative.CreateMediaBuyRequest"
    assert canonical in roots
    assert [branch.__module__ for branch in roots[canonical]._branch_models()] == [  # type: ignore[attr-defined]
        "adcp.types.canonical_creative"
    ] * 3


def test_a_branch_keeps_its_own_shape_rather_than_its_siblings() -> None:
    """A branch inherits the hook and must not validate as the union.

    The deleted override tested ``cls in arms`` for this, which is correct for
    an override and silently wrong for a core-schema hook: membership admits
    both "is a branch" and "is an unrelated subclass of the base", and only the
    second matters once the schema itself is being replaced. The hook instead
    asks whether the class DECLARES the method, which separates them.

    Graded by what a refusal SAYS. A branch asked to validate ``{}`` reports the
    fields IT requires; a branch that had picked up the union's schema would
    report the combinator, having tried every sibling.
    """
    graded = _graded_roots()
    assert graded, "the derivation selected no root to grade"

    branches = 0
    for name, root in sorted(graded.items()):
        combinator = root._branch_combinator()  # type: ignore[attr-defined]
        for branch in root._branch_models():  # type: ignore[attr-defined]
            assert "_branch_models" not in branch.__dict__, (name, branch.__name__)
            with pytest.raises(ValidationError) as caught:
                branch.model_validate({})
            assert combinator not in _keywords(caught.value), (
                f"{branch.__name__} refused with {combinator!r}, so it validates as "
                "the union rather than as itself"
            )
            branches += 1

    assert branches >= 49, f"only {branches} branches graded"


def test_ignoring_unknown_fields_cannot_make_a_branch_vacuously_satisfiable() -> None:
    """``extra="ignore"`` must not turn an unrecognised document into a valid one.

    Most of these models ignore extras: ``AdCPBaseModel`` is
    ``extra="ignore"``, and the generated response bases are ``extra="allow"``
    where their schemas say ``additionalProperties: true``. Under either
    setting, a branch that requires NOTHING matches every document -- pydantic
    drops or files the unknown keys and the branch is satisfied -- so one such
    branch would make its root accept anything while still looking dispatched.

    Asserted on the live models rather than reasoned about, because the property
    depends on the requiredness each branch ended up with after every pass that
    edits it, and a redeclaration that re-added a default would take it away.
    """
    roots = _roots_with_branches()
    assert roots, "the derivation selected no root"

    ignoring = {
        name: root for name, root in roots.items() if root.model_config.get("extra") != "forbid"
    }
    assert ignoring, "no root with branches tolerates an unknown field"

    for name, root in sorted(ignoring.items()):
        for branch in root._branch_models():  # type: ignore[attr-defined]
            required = {field for field, info in branch.model_fields.items() if info.is_required()}
            assert required, f"{name}: {branch.__name__} requires nothing, so it matches anything"

        # And the whole root, end to end: a document of nothing but unknown keys
        # is refused rather than emptied into a branch.
        with pytest.raises(ValidationError):
            root.model_validate({"totally": "wrong", "unknown": [1, 2]})
